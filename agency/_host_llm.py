"""Spec 279 Slice 1 — host-LLM delegation envelope.

When the AnthropicDriver isn't capable (no ``ANTHROPIC_API_KEY`` + no
injected client), ``driver.backend()`` returns ``"none"`` and
``driver.complete`` raises ``AUTH_FAILED``. Today verbs that wrap the
driver either crash, wrap that as ``ok=False``, or degrade to a lossy
scaffold path — the intent is lost.

But agency runs INSIDE Claude Code — the host IS an LLM. The correct
fallback hands inference BACK to the host, lets it run the model with
its own keys/quotas, and resumes the verb with the result. The
provenance moat stays intact (one Invocation node per delegated
round-trip; the ``outcome`` flips from ``"host_delegated"`` →
``"host_resumed"``), and the verb's contract is the same regardless of
who actually ran the LLM.

This module ships the typed ``HostLLMRequest`` envelope + the
``complete_or_delegate`` boundary helper every LLM-using verb wraps.
Three branches:

1. ``host_completion`` is given → wrap as
   ``Completion(stop_reason="host_provided")`` (resume path; wins
   regardless of driver state).
2. ``driver.backend() != "none"`` → call ``driver.complete(...)``
   (Spec 147 Slice 1; backwards-compatible direct path).
3. else → return ``HostLLMRequest{kind="llm_delegate", ...}`` so the
   caller delegates to the host.

The verb's caller (Claude Code) recognises the ``kind="llm_delegate"``
envelope on the wire, runs inference with the documented shape
(messages + system; optional ``output_schema``), and calls the verb
again with the result passed via ``host_completion``.

Subsequent slices add:

- Slice 2 — ``output_schema`` validation on ``host_completion["parsed"]``
  (today Slice 1 trusts the host).
- Slice 2.x — managed-agents session hand-off (Spec 248 / 252) when the
  host hands a full sub-session back, not just a single completion.
- Slice 3 — ``continuation_token`` as a graph node (multi-turn resume
  with tool use).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from agency._drivers._anthropic import Completion


HOST_DELEGATE_KIND = "llm_delegate"
DEFAULT_MAX_TOKENS = 8000


@dataclass(frozen=True)
class HostLLMRequest:
    """The boundary helper returns this when the driver backend is
    ``"none"``. The wire signal ``kind="llm_delegate"`` tells Claude
    Code (the host) to run inference with the documented shape and
    call the verb again, passing the result via ``host_completion``.

    ``continuation_token`` is opaque to the host but stable across the
    delegation round-trip — the verb mints it on first call, stores
    any state it needs in the graph keyed by the token, and looks it
    up on resume. Default shape (``make_continuation_token``):
    SHA-256 of ``(intent_id, verb_name, json(args)[:200])`` —
    deterministic so retries don't multiply, opaque so the host can't
    forge one for a different verb without seeing the args.

    Frozen so the envelope can't be mutated after construction
    (provenance: the verb records exactly this shape into the
    Invocation node).
    """

    kind: str
    messages: tuple[dict, ...]
    system: str
    continuation_token: str
    output_schema: dict | None = None
    model_hint: str | None = None
    max_tokens: int = DEFAULT_MAX_TOKENS

    def __post_init__(self) -> None:
        if self.kind != HOST_DELEGATE_KIND:
            raise ValueError(
                f"kind must be {HOST_DELEGATE_KIND!r}, got {self.kind!r}")
        if not isinstance(self.messages, tuple):
            raise TypeError(
                f"messages must be a tuple (frozen), got "
                f"{type(self.messages).__name__}")
        if not isinstance(self.continuation_token, str) or not self.continuation_token:
            raise ValueError(
                "continuation_token must be a non-empty string — the verb "
                "mints it via `make_continuation_token` (or supplies its own).")

    def to_dict(self) -> dict:
        """Wire-shape dict for the verb's return envelope. ``kind`` is
        emitted first so the host dispatcher can route on the first
        few bytes without parsing the rest of the payload."""
        out: dict = {
            "kind": self.kind,
            "continuation_token": self.continuation_token,
            "messages": list(self.messages),
            "system": self.system,
            "max_tokens": self.max_tokens,
        }
        if self.output_schema is not None:
            out["output_schema"] = self.output_schema
        if self.model_hint is not None:
            out["model_hint"] = self.model_hint
        return out


def make_continuation_token(
    intent_id: str, verb_name: str, args: dict | None = None,
) -> str:
    """Mint the default continuation token: SHA-256 hex (first 32
    chars) of ``(intent_id, verb_name, json(args, sort_keys)[:200])``.

    Deterministic so a retry of the same verb call against the same
    intent + args produces the same token — the host can't cause a
    duplicate Invocation node by re-sending. Opaque so the host can't
    forge one for a different verb without seeing the args (Spec 279
    failure mode: "token forgery").
    """
    args_blob = json.dumps(
        args or {}, sort_keys=True, separators=(",", ":"))[:200]
    blob = f"{intent_id}|{verb_name}|{args_blob}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]


def _derive_fallback_token(
    messages: list[dict], system: str, model_hint: str | None,
) -> str:
    """Derive a continuation token from the request shape itself when
    the verb doesn't supply one. Still deterministic — same request →
    same token. Used by ``complete_or_delegate`` so the helper is
    usable from tests and from verbs that don't yet hook into the
    intent system; real verbs SHOULD supply their own via
    ``make_continuation_token``."""
    payload = {
        "messages": messages,
        "system": system,
        "model_hint": model_hint,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]


class HostDelegateError(Exception):
    """Typed failure raised at the resume boundary when the host's
    ``host_completion`` is malformed or violates the contract.
    Maps to Spec 151 ``Codes.HOST_DELEGATE_*`` codes:

    - ``MALFORMED`` — ``host_completion`` is not a dict, or missing the
      required ``text`` field.
    - ``SCHEMA_FAIL`` — ``output_schema`` was supplied at request time
      but ``host_completion["parsed"]`` is missing or doesn't validate
      (Slice 2; Slice 1 trusts the host).
    - ``TIMEOUT`` — the verb's continuation_token has expired before
      resume (Slice 3 introduces the token TTL).
    """

    MALFORMED = "host_delegate_malformed"
    SCHEMA_FAIL = "host_delegate_schema_fail"
    TIMEOUT = "host_delegate_timeout"

    def __init__(self, code: str, message: str = "",
                 detail: dict | None = None):
        self.code = code
        self.detail = detail or {}
        super().__init__(f"{code}: {message}" if message else code)


def _messages_to_sample_input(messages: list[dict]) -> list[str]:
    """Flatten anthropic-style ``[{role, content}]`` to the ``str`` sequence
    ``ctx.sample`` accepts (system is passed separately). Slice 1 keeps it
    simple: the non-system message contents, in order."""
    return [str(m.get("content", "")) for m in messages
            if m.get("role") != "system"]


def complete_or_delegate(
    driver: Any,
    *,
    messages: list[dict],
    system: str = "",
    output_schema: dict | None = None,
    host_completion: dict | None = None,
    model_hint: str | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    continuation_token: str | None = None,
    host: Any = None,
) -> Completion | HostLLMRequest:
    """The boundary helper every LLM-using verb wraps. Four branches
    (the resume path always wins; then driver, then host sampling, then the
    delegate envelope):

    1. ``host_completion`` is given — the host already ran inference
       and called the verb again. Wrap as ``Completion(text=…,
       stop_reason="host_provided", parsed=…)``. Wins regardless of
       driver state, so a retry with ``host_completion`` keeps the
       verb's flow on the resume rail.

    2. ``driver.backend() != "none"`` — the AnthropicDriver is capable;
       call ``driver.complete(...)`` and return its ``Completion``
       (Spec 147 Slice 1). Backwards-compatible direct path:
       behavior is identical to a bare ``driver.complete(...)`` call.

    3. else — driver backend is ``"none"``; return a
       ``HostLLMRequest`` envelope. The wrapping verb returns it as
       part of its response so the host (Claude Code) recognises
       ``kind="llm_delegate"``, runs inference, and calls the verb
       again with the result via ``host_completion``.

    Raises ``HostDelegateError(MALFORMED)`` if ``host_completion`` is
    given but is not a dict or lacks a ``text`` field — Slice 1 trusts
    the host on schema; Slice 2 will validate
    ``host_completion["parsed"]`` against ``output_schema``.
    """
    # Branch 1 (resume) — wins over everything else.
    if host_completion is not None:
        if not isinstance(host_completion, dict) or "text" not in host_completion:
            raise HostDelegateError(
                HostDelegateError.MALFORMED,
                "host_completion missing required `text` field",
                {"received_keys":
                    sorted(host_completion) if isinstance(host_completion, dict)
                    else None})
        return Completion(
            text=host_completion["text"],
            stop_reason="host_provided",
            usage=host_completion.get("usage", {}),
            model=host_completion.get("model", "host"),
            request_id=host_completion.get("request_id", ""),
            parsed=host_completion.get("parsed"),
        )

    # Branch 2 (driver capable) — Spec 147 Slice 1 direct path. An explicitly
    # wired API-key driver wins (deterministic + testable) over sampling.
    if driver.backend() != "none":
        return driver.complete(
            messages=messages,
            system=system,
            output_schema=output_schema,
            max_tokens=max_tokens,
        )

    # Branch 3 (host sampling) — Spec 285: real MCP sampling when a capable
    # host Context is bound + sampling_enabled. Returns a Completion with
    # stop_reason="host_sampled" (the third inference path, distinct from
    # host_provided/host_sampled-vs-delegate in provenance). Falls THROUGH to
    # the envelope when the host can't sample (HostUnavailable) — Spec 279 is
    # the capability-negotiated fallback, not removed.
    if host is not None and host.can_sample():
        from ._host_bridge import HostUnavailable
        try:
            return host.sample(
                _messages_to_sample_input(messages),
                system=system or None,
                max_tokens=max_tokens,
            )
        except HostUnavailable:
            pass

    # Branch 4 (delegate) — emit the envelope.
    token = continuation_token or _derive_fallback_token(
        messages=messages, system=system, model_hint=model_hint)
    return HostLLMRequest(
        kind=HOST_DELEGATE_KIND,
        messages=tuple(messages),
        system=system,
        continuation_token=token,
        output_schema=output_schema,
        model_hint=model_hint,
        max_tokens=max_tokens,
    )
