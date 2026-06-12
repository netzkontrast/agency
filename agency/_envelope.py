"""Spec 146 Slice 1 — engine-output-prefix discipline.

The Claude API's prompt-caching is a prefix-match: any byte change anywhere in
the cached prefix invalidates everything after it. Substrate-tool responses
that interpolate `datetime.now()` ISO timestamps + intent-id UUIDs into the
HEAD of every response silently invalidate every wrapping driver's cache.

This module ships the typed envelope split:

    ResponseEnvelope(prefix: dict, body: dict)

Per-build state (schema_version, capability_set hash, ontology hash, wire
contract, capability list) lives in `prefix` — byte-stable across calls when
the registry has not changed. Per-call state (timestamps, intent IDs, state,
counters, cursors) lives in `body`.

The canonical serializer (`canonical_json`) emits prefix keys (sorted)
BEFORE body keys (sorted), with compact JSON separators — so the wrapping
LLM driver can apply `cache_control: {"type": "ephemeral"}` to the prefix
prefix-match cleanly.

Subsequent slices add:
- Slice 2.1 — `_check_response_prefix` AST lint rule (Spec 067 family)
- Slice 2.2 — prefix-lint baseline + WARN→error CI gate (shipped)
- Slice 3 — `agency_doctor.prefix_stability` + Claude-API cache-hit invariant
- Slice 4 — `PREFIX_BUDGET_EXCEEDED` hard-fail at MAX_PREFIX_TOKENS

Spec 154 Slice 2 — `capture_body_overflow(env, max_body_tokens, counter)`
wires the pure `agency/_overflow.py` capture library through the envelope.
The PREFIX is never touched (Spec 146 byte-stability invariant); only the
BODY half is summarised when its canonical serialization exceeds the
budget. The returned envelope's body becomes
`{_overflow_preview: head_blob, _overflow_handle: {...}}` and the wrapping
driver / agent can call `recall_overflow` (Slice 3) on the handle.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ResponseEnvelope:
    """Typed split of a substrate-tool response into a cache-friendly prefix
    and a per-call body. Keys MUST NOT overlap between halves."""

    prefix: dict
    body: dict

    def __post_init__(self) -> None:
        if not isinstance(self.prefix, dict):
            raise TypeError(
                f"prefix must be dict, got {type(self.prefix).__name__}")
        if not isinstance(self.body, dict):
            raise TypeError(
                f"body must be dict, got {type(self.body).__name__}")
        # JSON object keys MUST be strings (Codex review on PR #134
        # round 4). A non-string key like `1` would coerce to `"1"` on
        # the wire and silently collide with a string `"1"` on the
        # other half — the body value could overwrite the prefix value
        # (or vice versa) without the overlap check ever firing.
        for half_name, half in (("prefix", self.prefix), ("body", self.body)):
            for k in half:
                if not isinstance(k, str):
                    raise TypeError(
                        f"{half_name} keys must be str (JSON object key "
                        f"contract), got {type(k).__name__}={k!r}")

    def to_dict(self) -> dict:
        """Merge prefix + body, sorted keys within each half, prefix keys first.
        Raises when prefix + body share a key (the split is the contract)."""
        overlap = set(self.prefix).intersection(self.body)
        if overlap:
            raise ValueError(
                f"prefix/body key overlap: {sorted(overlap)} — Spec 146 "
                f"contract violated; pick exactly one side per key.")
        out: dict = {}
        for k in sorted(self.prefix):
            out[k] = self.prefix[k]
        for k in sorted(self.body):
            out[k] = self.body[k]
        return out

    def prefix_hash(self) -> str:
        """SHA-256 hex of the canonical-JSON prefix. Deterministic across
        dict-insertion orders; unaffected by body changes."""
        blob = json.dumps(self.prefix, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def canonical_json(env: ResponseEnvelope) -> str:
    """Serialize an envelope to canonical JSON: prefix keys (sorted) before
    body keys (sorted), compact separators (no insignificant whitespace).
    Two envelopes with the same {prefix, body} content yield byte-identical
    output regardless of how their dicts were constructed.

    Implementation: serialize prefix and body INDEPENDENTLY (each
    `sort_keys=True`) and splice them so prefix bytes always precede body
    bytes. A naive `json.dumps(env.to_dict(), sort_keys=True, ...)` would
    re-sort prefix+body keys GLOBALLY, letting a body key like `"delta"`
    serialize ahead of a prefix key like `"schema_version"` — breaking
    the prefix-match cache invariant (Codex review on PR #134, P1)."""
    overlap = set(env.prefix).intersection(env.body)
    if overlap:
        raise ValueError(
            f"prefix/body key overlap: {sorted(overlap)} — Spec 146 "
            f"contract violated; pick exactly one side per key.")
    prefix_blob = json.dumps(env.prefix, sort_keys=True, separators=(",", ":"))
    body_blob = json.dumps(env.body, sort_keys=True, separators=(",", ":"))
    inner_prefix = prefix_blob[1:-1]
    inner_body = body_blob[1:-1]
    if inner_prefix and inner_body:
        return "{" + inner_prefix + "," + inner_body + "}"
    return "{" + inner_prefix + inner_body + "}"


def capability_set_hash(
    names: list[str] | set[str] | tuple[str, ...],
    signatures: dict[str, str] | None = None,
) -> str:
    """Deterministic hash of the capability surface.

    Order-invariant on `names` (set semantics — registering the same caps in
    a different order MUST yield the same hash). When `signatures` is given
    (per Spec 146 Open-Q 3: names + signatures), a signature change is a
    wire-shape change (Spec 019) and rolls the hash so the wrapping driver's
    cache invalidates correctly.
    """
    payload: dict = {"names": sorted(set(names))}
    if signatures is not None:
        payload["signatures"] = {k: signatures[k] for k in sorted(signatures)}
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def ontology_hash(ontology: dict[str, list[str]]) -> str:
    """Deterministic hash of an ontology shape (node-type → property keys).
    Order-invariant on both the top-level node-type keys AND the per-type
    property lists."""
    normalized = {k: sorted(ontology[k]) for k in sorted(ontology)}
    blob = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ── Spec 154 Slice 2 — body-half overflow capture ────────────────────────
@dataclass(frozen=True)
class BodyOverflowResult:
    """Typed return of `capture_body_overflow`. `envelope` is the
    (possibly-summarised) envelope ready to wire; `handle` is the typed
    OverflowHandle when capture fired, else None."""

    envelope: "ResponseEnvelope"
    handle: Optional[Any]                                         # OverflowHandle | None


def capture_body_overflow(
    env: ResponseEnvelope, *,
    max_body_tokens: int,
    counter: Any,
) -> BodyOverflowResult:
    """Inspect the envelope's BODY against `max_body_tokens`; either pass
    the envelope through unchanged OR return a new envelope whose body
    is the summary shape `{_overflow_preview: head, _overflow_handle:
    {...}}`. The PREFIX is byte-identical (Spec 146 invariant).

    `counter` is anything `agency/_overflow.py:_as_counter_fn` accepts
    (callable `(text) -> int` OR Spec 082 `TokenCounter.count(text)`).
    `max_body_tokens` MUST be ≥ 0; negative raises ValueError."""
    if max_body_tokens < 0:
        raise ValueError(f"max_body_tokens must be ≥ 0, got {max_body_tokens}")
    from ._overflow import capture_overflow, OverflowHandle
    body_blob = json.dumps(env.body, sort_keys=True, separators=(",", ":"))
    res = capture_overflow(body_blob, max_tokens=max_body_tokens,
                            counter=counter)
    if not res.truncated:
        return BodyOverflowResult(envelope=env, handle=None)
    handle = OverflowHandle(
        recall_handle="",                                          # Slice 3 wires to Artefact id
        total_tokens=res.total_tokens,
        returned_tokens=res.returned_tokens,
        truncated=True,
    )
    summarised = {
        "_overflow_preview": res.head,
        "_overflow_handle": {
            "recall_handle": handle.recall_handle,
            "total_tokens": handle.total_tokens,
            "returned_tokens": handle.returned_tokens,
            "truncated": handle.truncated,
        },
    }
    return BodyOverflowResult(
        envelope=ResponseEnvelope(prefix=env.prefix, body=summarised),
        handle=handle,
    )
