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
- Slice 2 — `_check_response_prefix` AST lint rule (Spec 067 family)
- Slice 3 — `agency_doctor.prefix_stability` + Claude-API cache-hit invariant
- Slice 4 — `PREFIX_BUDGET_EXCEEDED` hard-fail at MAX_PREFIX_TOKENS
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


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
    output regardless of how their dicts were constructed."""
    return json.dumps(env.to_dict(), sort_keys=True, separators=(",", ":"))


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
