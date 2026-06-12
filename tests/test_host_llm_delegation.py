"""Spec 279 Slice 1 — host-LLM delegation envelope.

Tests the three branches of ``complete_or_delegate``:

1. ``host_completion`` provided → ``Completion(stop_reason="host_provided")``
   (resume path; wins regardless of driver state).
2. driver backend != "none" → ``driver.complete(...)`` direct
   (Spec 147 Slice 1 backwards-compat).
3. driver backend == "none" → ``HostLLMRequest{kind="llm_delegate", ...}``
   (delegate path; host runs inference).

Plus the surrounding invariants:

- ``HostLLMRequest`` is frozen + typed (provenance: the verb records
  exactly this shape into the Invocation node).
- ``continuation_token`` is deterministic per (intent_id, verb_name, args)
  — retries don't multiply (Spec 279 failure mode: provenance split).
- Malformed ``host_completion`` raises ``HostDelegateError(MALFORMED)``.
"""
from __future__ import annotations

import dataclasses

import pytest

from agency._drivers._anthropic import Completion
from agency._host_llm import (
    DEFAULT_MAX_TOKENS,
    HOST_DELEGATE_KIND,
    HostDelegateError,
    HostLLMRequest,
    complete_or_delegate,
    make_continuation_token,
)


# ── stub drivers ───────────────────────────────────────────────────────────
class _NoBackendDriver:
    """Mimics AnthropicDriver with no key + no client: backend() == 'none'."""

    def backend(self) -> str:
        return "none"

    def complete(self, **_kwargs):                                # pragma: no cover
        raise AssertionError("Branch 3 must NOT call driver.complete")


class _CapableDriver:
    """Mimics AnthropicDriver with a key (or injected client): backend() == 'anthropic'."""

    def __init__(self, completion: Completion | None = None):
        self._completion = completion or Completion(
            text="from-driver", stop_reason="end_turn", model="claude-test")
        self.last_call: dict | None = None

    def backend(self) -> str:
        return "anthropic"

    def complete(self, **kwargs):
        self.last_call = kwargs
        return self._completion


# ── HostLLMRequest shape ──────────────────────────────────────────────────
def test_host_llm_request_is_frozen():
    """Provenance: the verb records EXACTLY the envelope shape into the
    Invocation node. A mutable envelope could drift between mint and
    record."""
    req = HostLLMRequest(
        kind=HOST_DELEGATE_KIND,
        messages=({"role": "user", "content": "hello"},),
        system="be helpful",
        continuation_token="abc123",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        req.system = "mutated"                                    # type: ignore[misc]


def test_host_llm_request_rejects_wrong_kind():
    """The wire signal is `kind="llm_delegate"`. Any other value is a
    contract violation — the host wouldn't route it as a delegation."""
    with pytest.raises(ValueError, match="kind must be"):
        HostLLMRequest(
            kind="something_else",
            messages=(),
            system="",
            continuation_token="abc",
        )


def test_host_llm_request_rejects_non_tuple_messages():
    """Messages must be a tuple (frozen-friendly); a mutable list would
    let the envelope's contents drift after mint."""
    with pytest.raises(TypeError, match="tuple"):
        HostLLMRequest(
            kind=HOST_DELEGATE_KIND,
            messages=[{"role": "user", "content": "x"}],          # type: ignore[arg-type]
            system="",
            continuation_token="abc",
        )


def test_host_llm_request_rejects_empty_token():
    """A blank or missing continuation_token means the verb can't
    resume — reject at construction."""
    with pytest.raises(ValueError, match="continuation_token"):
        HostLLMRequest(
            kind=HOST_DELEGATE_KIND,
            messages=(),
            system="",
            continuation_token="",
        )


def test_host_llm_request_to_dict_emits_kind_first():
    """The wire format places `kind` first so the host's dispatcher can
    route on the leading bytes without parsing the rest. The dict
    preserves insertion order (Python 3.7+ guarantee)."""
    req = HostLLMRequest(
        kind=HOST_DELEGATE_KIND,
        messages=({"role": "user", "content": "x"},),
        system="sys",
        continuation_token="tok",
        model_hint="claude-opus-4-7",
        max_tokens=4000,
    )
    d = req.to_dict()
    assert list(d)[0] == "kind"
    assert d["kind"] == HOST_DELEGATE_KIND
    assert d["continuation_token"] == "tok"
    assert d["messages"] == [{"role": "user", "content": "x"}]
    assert d["model_hint"] == "claude-opus-4-7"
    assert d["max_tokens"] == 4000


def test_host_llm_request_to_dict_omits_optional_fields_when_none():
    """`output_schema` and `model_hint` are optional; their absence
    keeps the prefix tight (Spec 146)."""
    req = HostLLMRequest(
        kind=HOST_DELEGATE_KIND,
        messages=(),
        system="",
        continuation_token="tok",
    )
    d = req.to_dict()
    assert "output_schema" not in d
    assert "model_hint" not in d


# ── make_continuation_token determinism ────────────────────────────────────
def test_continuation_token_is_deterministic():
    """Same (intent_id, verb_name, args) → same token. Retries don't
    mint a duplicate Invocation node (Spec 279 single-Invocation
    invariant)."""
    a = make_continuation_token("intent-1", "novel.generate_scene",
                                 {"scene_id": "s1"})
    b = make_continuation_token("intent-1", "novel.generate_scene",
                                 {"scene_id": "s1"})
    assert a == b
    assert len(a) == 32                                            # SHA-256 hex, 32-char prefix


def test_continuation_token_changes_with_args():
    """Different args → different token. The host can't forge a token
    by reusing one from another verb call (token-forgery defense)."""
    a = make_continuation_token("intent-1", "novel.generate_scene",
                                 {"scene_id": "s1"})
    b = make_continuation_token("intent-1", "novel.generate_scene",
                                 {"scene_id": "s2"})
    assert a != b


def test_continuation_token_changes_with_verb_name():
    """Different verbs over the same intent → different tokens.
    Provenance: the token is bound to the verb."""
    a = make_continuation_token("intent-1", "novel.generate_scene", {})
    b = make_continuation_token("intent-1", "novel.editorial_review", {})
    assert a != b


def test_continuation_token_changes_with_intent_id():
    """The intent_id is part of the binding — a different intent must
    yield a different token even when verb + args match."""
    a = make_continuation_token("intent-1", "v", {"k": "v"})
    b = make_continuation_token("intent-2", "v", {"k": "v"})
    assert a != b


# ── Branch 2: driver capable → Completion ─────────────────────────────────
def test_complete_or_delegate_uses_capable_driver():
    """When `driver.backend() != "none"` and no `host_completion` is
    supplied, behavior is identical to Spec 147 Slice 1: returns the
    driver's Completion. Backwards-compat invariant."""
    driver = _CapableDriver()
    out = complete_or_delegate(
        driver,
        messages=[{"role": "user", "content": "hi"}],
        system="be brief",
    )
    assert isinstance(out, Completion)
    assert out.text == "from-driver"
    assert driver.last_call is not None
    assert driver.last_call["messages"] == [
        {"role": "user", "content": "hi"}]
    assert driver.last_call["system"] == "be brief"


def test_complete_or_delegate_forwards_output_schema_to_driver():
    """When the driver path runs, `output_schema` flows through to
    `driver.complete` so structured-output paths still work."""
    driver = _CapableDriver()
    schema = {"type": "object", "properties": {"x": {"type": "string"}}}
    complete_or_delegate(
        driver,
        messages=[{"role": "user", "content": "x"}],
        output_schema=schema,
    )
    assert driver.last_call is not None
    assert driver.last_call["output_schema"] == schema


# ── Branch 3: no-backend driver → HostLLMRequest ──────────────────────────
def test_complete_or_delegate_emits_host_request_when_no_backend():
    """When `driver.backend() == "none"`, the helper returns a
    `HostLLMRequest` envelope with `kind="llm_delegate"`. The wrapping
    verb returns this so Claude Code recognises the delegation signal."""
    driver = _NoBackendDriver()
    out = complete_or_delegate(
        driver,
        messages=[{"role": "user", "content": "write a scene"}],
        system="you are a novelist",
    )
    assert isinstance(out, HostLLMRequest)
    assert out.kind == HOST_DELEGATE_KIND
    assert out.system == "you are a novelist"
    assert out.messages == ({"role": "user", "content": "write a scene"},)
    assert out.continuation_token != ""
    assert len(out.continuation_token) == 32


def test_complete_or_delegate_uses_provided_continuation_token():
    """When the verb supplies its own continuation_token (the canonical
    pattern — minted via `make_continuation_token`), the envelope
    carries that token verbatim."""
    driver = _NoBackendDriver()
    tok = make_continuation_token("intent-1", "v", {"a": 1})
    out = complete_or_delegate(
        driver,
        messages=[{"role": "user", "content": "x"}],
        continuation_token=tok,
    )
    assert isinstance(out, HostLLMRequest)
    assert out.continuation_token == tok


def test_complete_or_delegate_delegate_path_carries_output_schema_and_hints():
    """The envelope includes everything the host needs to run inference
    correctly: messages, system, output_schema, model_hint, max_tokens."""
    driver = _NoBackendDriver()
    schema = {"type": "object", "required": ["scene"]}
    out = complete_or_delegate(
        driver,
        messages=[{"role": "user", "content": "x"}],
        system="sys",
        output_schema=schema,
        model_hint="claude-sonnet-4-6",
        max_tokens=4000,
    )
    assert isinstance(out, HostLLMRequest)
    assert out.output_schema == schema
    assert out.model_hint == "claude-sonnet-4-6"
    assert out.max_tokens == 4000


# ── Branch 1: host_completion → Completion(host_provided) ─────────────────
def test_host_completion_returns_completion_with_host_provided_stop():
    """When the host has run inference and called the verb again with
    `host_completion`, return a `Completion(stop_reason="host_provided")`.
    The verb's flow is the same as if the driver had returned it."""
    driver = _NoBackendDriver()
    out = complete_or_delegate(
        driver,
        messages=[{"role": "user", "content": "x"}],
        host_completion={"text": "<the scene>"},
    )
    assert isinstance(out, Completion)
    assert out.text == "<the scene>"
    assert out.stop_reason == "host_provided"


def test_host_completion_wins_over_capable_driver():
    """A retry with `host_completion` keeps the verb on the resume rail
    regardless of driver state — the helper must not re-invoke the
    driver when the host has already run inference."""
    driver = _CapableDriver()
    out = complete_or_delegate(
        driver,
        messages=[{"role": "user", "content": "x"}],
        host_completion={"text": "<host-text>"},
    )
    assert isinstance(out, Completion)
    assert out.text == "<host-text>"
    assert out.stop_reason == "host_provided"
    assert driver.last_call is None, \
        "driver.complete must NOT be called when host_completion is given"


def test_host_completion_carries_parsed_field():
    """When `host_completion["parsed"]` is supplied (structured-output
    path), it flows through to `Completion.parsed`. Slice 2 will
    validate against `output_schema`; Slice 1 trusts the host."""
    driver = _CapableDriver()
    out = complete_or_delegate(
        driver,
        messages=[],
        host_completion={"text": '{"x":1}', "parsed": {"x": 1}},
    )
    assert isinstance(out, Completion)
    assert out.parsed == {"x": 1}


def test_host_completion_missing_text_raises_malformed():
    """The host MUST supply `text`. Missing it is a protocol violation
    — Slice 1 surfaces `HostDelegateError(MALFORMED)` at the boundary
    so the wrapping verb maps it to `Codes.HOST_DELEGATE_MALFORMED`."""
    driver = _CapableDriver()
    with pytest.raises(HostDelegateError) as exc:
        complete_or_delegate(
            driver,
            messages=[],
            host_completion={"parsed": {"x": 1}},                  # no "text"
        )
    assert exc.value.code == HostDelegateError.MALFORMED


def test_host_completion_non_dict_raises_malformed():
    """A non-dict `host_completion` (e.g. the host returned a bare
    string by mistake) is malformed."""
    driver = _CapableDriver()
    with pytest.raises(HostDelegateError) as exc:
        complete_or_delegate(
            driver,
            messages=[],
            host_completion="<oops>",                              # type: ignore[arg-type]
        )
    assert exc.value.code == HostDelegateError.MALFORMED


# ── default max_tokens constant ────────────────────────────────────────────
def test_default_max_tokens_matches_documented_default():
    """Spec 279 documents `max_tokens=8000` as the Slice 1 default —
    a tunable budget (CLAUDE.md rule 8: documented, not a snapshot)."""
    assert DEFAULT_MAX_TOKENS == 8000
