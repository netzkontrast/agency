"""Spec 146 Slice 1 — engine-output-prefix discipline.

The Claude API's prompt-caching is a prefix-match — any byte change anywhere
in the prefix invalidates everything after it. Today substrate-tool
responses interpolate `datetime.now()` ISO timestamps + intent-id UUIDs
into the HEAD of every response, silently invalidating every wrapper's
cache.

Slice 1 ships the envelope split: `ResponseEnvelope{prefix, body}` with
a deterministic serializer (prefix keys serialized first, sorted, alongside
body keys). Per-call state (timestamps, intent_ids, state machine output,
cursor) lands in `body`; per-build state (schema_version, capability_set
hash, ontology_hash) lands in `prefix`. `agency_welcome` is rewired
through the envelope.

Subsequent slices add:
- Slice 2 — `_check_response_prefix` lint rule (Spec 067 family AST)
- Slice 3 — `agency_doctor.prefix_stability` + Claude-API cache-hit invariant
- Slice 4 — `PREFIX_BUDGET_EXCEEDED` hard-fail at MAX_PREFIX_TOKENS

The test suite asserts INVARIANTS + RELATIONSHIPS per CLAUDE.md rule 8 —
no pinned counts or magic numbers.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agency._envelope import (
    ResponseEnvelope,
    canonical_json,
    capability_set_hash,
    ontology_hash,
)


# ── ResponseEnvelope shape + serialization ───────────────────────────────────
def test_envelope_is_a_typed_dataclass_with_prefix_and_body():
    env = ResponseEnvelope(prefix={"k": 1}, body={"j": 2})
    assert env.prefix == {"k": 1}
    assert env.body == {"j": 2}


def test_envelope_rejects_non_dict_prefix_or_body():
    # Boundary protocol (Spec 002) — typed shapes only, no None / list / str slip-through.
    with pytest.raises(TypeError):
        ResponseEnvelope(prefix="oops", body={})            # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ResponseEnvelope(prefix={}, body=["oops"])          # type: ignore[arg-type]


def test_envelope_to_dict_merges_prefix_and_body():
    env = ResponseEnvelope(prefix={"a": 1, "b": 2}, body={"c": 3})
    out = env.to_dict()
    assert out["a"] == 1 and out["b"] == 2 and out["c"] == 3


def test_envelope_to_dict_rejects_prefix_body_key_overlap():
    # The split is the contract — a key in BOTH halves is a doctrine violation.
    env = ResponseEnvelope(prefix={"x": 1}, body={"x": 2})
    with pytest.raises(ValueError, match="overlap"):
        env.to_dict()


# ── canonical JSON: prefix keys come first, sorted ──────────────────────────
def test_canonical_json_serializes_prefix_keys_before_body_keys():
    env = ResponseEnvelope(prefix={"alpha": 1, "beta": 2}, body={"gamma": 3, "delta": 4})
    blob = canonical_json(env)
    # decoded order matches encoded order (Python dict preserves insertion)
    decoded = json.loads(blob, object_pairs_hook=list)
    keys = [k for k, _ in decoded]
    # prefix keys (sorted) come BEFORE body keys (sorted)
    prefix_keys = sorted(env.prefix.keys())
    body_keys = sorted(env.body.keys())
    assert keys == prefix_keys + body_keys


def test_canonical_json_is_deterministic_across_dict_insertion_orders():
    a = ResponseEnvelope(prefix={"z": 1, "a": 2}, body={"y": 3, "b": 4})
    b = ResponseEnvelope(prefix={"a": 2, "z": 1}, body={"b": 4, "y": 3})
    assert canonical_json(a) == canonical_json(b)


def test_canonical_json_uses_compact_separators():
    # Cache-friendly: no insignificant whitespace that would diverge between
    # platforms or serializers and break the byte-identical prefix invariant.
    env = ResponseEnvelope(prefix={"k": "v"}, body={"j": "w"})
    blob = canonical_json(env)
    assert ", " not in blob and ": " not in blob


# ── prefix hash + body isolation ─────────────────────────────────────────────
def test_prefix_hash_is_deterministic():
    a = ResponseEnvelope(prefix={"capability_set_hash": "abc", "schema_version": 1}, body={})
    b = ResponseEnvelope(prefix={"schema_version": 1, "capability_set_hash": "abc"}, body={})
    assert a.prefix_hash() == b.prefix_hash()
    assert len(a.prefix_hash()) == 64                          # sha256 hex


def test_prefix_hash_changes_when_prefix_changes():
    a = ResponseEnvelope(prefix={"capability_set_hash": "abc"}, body={})
    b = ResponseEnvelope(prefix={"capability_set_hash": "xyz"}, body={})
    assert a.prefix_hash() != b.prefix_hash()


def test_prefix_hash_unaffected_by_body_changes():
    a = ResponseEnvelope(prefix={"capability_set_hash": "abc"}, body={"intent_id": "i1"})
    b = ResponseEnvelope(prefix={"capability_set_hash": "abc"}, body={"intent_id": "i2"})
    # Body churn (per-call) must not invalidate the cache prefix.
    assert a.prefix_hash() == b.prefix_hash()


# ── capability_set_hash + ontology_hash ──────────────────────────────────────
def test_capability_set_hash_is_a_function_of_registry_names():
    a = capability_set_hash(["analyze", "research"])
    b = capability_set_hash(["research", "analyze"])           # order-invariant
    c = capability_set_hash(["analyze", "research", "delegate"])
    assert a == b                                              # sets, not lists
    assert a != c                                              # set CHANGED → hash CHANGES
    assert len(a) == 64                                        # sha256 hex


def test_capability_set_hash_includes_verb_signatures_when_provided():
    # Spec 146 §Open Q 3 — names + signatures: a signature change IS a
    # wire-shape change (Spec 019) and must invalidate the cache.
    names_only = capability_set_hash(["analyze"])
    with_sig = capability_set_hash(
        ["analyze"], signatures={"analyze": "intent_id:str,agent_id:str"})
    with_sig2 = capability_set_hash(
        ["analyze"], signatures={"analyze": "intent_id:str,agent_id:str,scope:str"})
    assert names_only != with_sig                              # signature ADDED → differ
    assert with_sig != with_sig2                               # signature CHANGED → differ


def test_ontology_hash_is_deterministic_per_input():
    a = ontology_hash({"Intent": ["purpose", "deliverable"], "Artefact": ["uri"]})
    b = ontology_hash({"Artefact": ["uri"], "Intent": ["purpose", "deliverable"]})
    assert a == b                                              # order-invariant
    assert len(a) == 64


# ── agency_welcome wired through envelope (RED → GREEN integration) ─────────
def test_agency_welcome_prefix_excludes_per_call_state(tmp_path):
    """The welcome envelope's prefix must not contain timestamps, intent IDs,
    or any state that changes call-to-call when the registry is unchanged."""
    from agency.engine import Engine

    e = Engine(str(tmp_path / "agency.db"))
    mcp = e.build_mcp()
    welcome = _find_tool(mcp, "agency_welcome")
    out1 = welcome()
    # The Slice-1 contract: returned dict is an envelope merged-view with a
    # `_prefix_keys` discoverable field that lists which keys live in prefix.
    assert "_prefix_keys" in out1, (
        "Slice 1: agency_welcome must declare its prefix-vs-body split via "
        "`_prefix_keys` so wrappers can apply cache_control on the right slice.")
    prefix_keys = set(out1["_prefix_keys"])
    # Per-call state must NOT be in the prefix.
    forbidden_in_prefix = {"state", "intents_count", "last_intent", "db_path", "next"}
    assert prefix_keys.isdisjoint(forbidden_in_prefix), (
        f"prefix contains per-call keys: {prefix_keys & forbidden_in_prefix}")
    # Per-build state SHOULD be in the prefix.
    required_in_prefix = {"capability_set_hash", "ontology_hash", "schema_version",
                          "wire_contract", "capabilities"}
    assert required_in_prefix.issubset(prefix_keys), (
        f"prefix missing required keys: {required_in_prefix - prefix_keys}")


def test_agency_welcome_prefix_is_byte_stable_across_calls_when_registry_unchanged(tmp_path):
    """The cache-hit invariant in Slice 1's pure form: byte-stability.
    Slice 3 will add the Claude-API cache-read assertion."""
    from agency.engine import Engine

    e = Engine(str(tmp_path / "agency.db"))
    welcome = _find_tool(e.build_mcp(), "agency_welcome")
    out1 = welcome()
    out2 = welcome()
    # Slice the merged dict back into prefix-only via `_prefix_keys`.
    prefix1 = {k: out1[k] for k in out1["_prefix_keys"]}
    prefix2 = {k: out2[k] for k in out2["_prefix_keys"]}
    blob1 = json.dumps(prefix1, sort_keys=True, separators=(",", ":"))
    blob2 = json.dumps(prefix2, sort_keys=True, separators=(",", ":"))
    assert blob1 == blob2, (
        "prefix drifted across two calls with no registry change — Spec 146 "
        "invariant violated; check for datetime.now()/uuid4() in prefix builders.")


def _find_tool(mcp, name):
    """Locate a registered substrate tool by name."""
    for provider in getattr(mcp, "providers", ()):
        for key, tool in getattr(provider, "_components", {}).items():
            if not key.startswith("tool:"):
                continue
            if getattr(tool, "name", "") == name:
                # FastMCP wraps the original callable; invoke via .fn for the
                # raw dict return (no JSON-RPC envelope on the unit path).
                return getattr(tool, "fn", tool)
    raise AssertionError(f"tool {name!r} not found in mcp providers")


# ─────────────── Spec 154 Slice 2 — body-half overflow capture ───────────
# Wires the pure `agency/_overflow.py` library through `agency/_envelope.py`:
# `capture_body_overflow(env, max_body_tokens, counter)` returns a NEW
# ResponseEnvelope whose body is summarised when the body's canonical
# serialization exceeds the budget. The PREFIX is byte-identical (Spec 146
# invariant). When the body fits, the envelope is returned unchanged.
def _char_counter(text: str) -> int:
    """Test-friendly proxy: 1 char ≈ 1 token (deterministic; Spec 082-free)."""
    return len(text)


def test_capture_body_overflow_returns_envelope_unchanged_under_budget():
    """Body that fits the budget: same envelope returned, no overflow handle."""
    from agency._envelope import ResponseEnvelope, capture_body_overflow
    env = ResponseEnvelope(
        prefix={"schema_version": 1, "wire_contract": "search/get_schema/execute"},
        body={"intents": 3, "last_intent": "intent:x"})
    out = capture_body_overflow(env, max_body_tokens=10_000,
                                 counter=_char_counter)
    assert out.envelope.body == env.body
    assert out.handle is None
    # Byte-stability invariant: prefix dict is untouched.
    assert out.envelope.prefix == env.prefix


def test_capture_body_overflow_truncates_body_over_budget():
    """Body whose canonical JSON exceeds the budget: returned envelope's
    body is the captured shape `{_overflow_preview, _overflow_handle}`
    and `handle.truncated == True`."""
    from agency._envelope import ResponseEnvelope, capture_body_overflow
    env = ResponseEnvelope(
        prefix={"schema_version": 1},
        body={"transcript": "X" * 500})
    out = capture_body_overflow(env, max_body_tokens=80,
                                 counter=_char_counter)
    assert out.handle is not None
    assert out.handle.truncated is True
    # The body half is replaced by a summary shape that still serializes
    # under the budget.
    assert "_overflow_preview" in out.envelope.body
    assert "_overflow_handle" in out.envelope.body


def test_capture_body_overflow_prefix_is_byte_identical():
    """Spec 146 invariant: prefix bytes don't move regardless of body
    capture. canonical_json on the prefix-only sub-envelope yields the
    same bytes before and after."""
    import json
    from agency._envelope import (
        ResponseEnvelope, canonical_json, capture_body_overflow)
    prefix = {"capability_set_hash": "h", "schema_version": 1,
              "wire_contract": "search/get_schema/execute"}
    env = ResponseEnvelope(prefix=prefix, body={"large": "Y" * 10_000})
    blob_before = canonical_json(ResponseEnvelope(prefix=prefix, body={}))
    out = capture_body_overflow(env, max_body_tokens=120,
                                 counter=_char_counter)
    # Prefix dict object-equal AND its canonical-json bytes are unchanged.
    assert out.envelope.prefix == prefix
    blob_after = canonical_json(ResponseEnvelope(prefix=out.envelope.prefix,
                                                  body={}))
    assert blob_after == blob_before


def test_capture_body_overflow_handle_carries_token_counts():
    """The OverflowHandle on the envelope carries `total_tokens`,
    `returned_tokens`, `truncated` — wrapping driver uses them to
    decide whether to call `recall_overflow`."""
    from agency._envelope import ResponseEnvelope, capture_body_overflow
    env = ResponseEnvelope(prefix={"a": 1}, body={"big": "Z" * 400})
    out = capture_body_overflow(env, max_body_tokens=80,
                                 counter=_char_counter)
    assert out.handle.total_tokens > 80
    assert out.handle.returned_tokens <= 80
    assert out.handle.truncated is True


def test_capture_body_overflow_zero_budget_yields_empty_preview():
    """Edge: max_body_tokens=0 still returns a valid envelope (no crash);
    handle.truncated=True, preview is empty."""
    from agency._envelope import ResponseEnvelope, capture_body_overflow
    env = ResponseEnvelope(prefix={"a": 1}, body={"k": "v"})
    out = capture_body_overflow(env, max_body_tokens=0,
                                 counter=_char_counter)
    assert out.handle is not None
    assert out.handle.truncated is True
    assert out.envelope.body["_overflow_preview"] == ""


def test_capture_body_overflow_rejects_negative_budget():
    """A negative budget is a programming error — fail loud."""
    from agency._envelope import ResponseEnvelope, capture_body_overflow
    env = ResponseEnvelope(prefix={"a": 1}, body={"k": "v"})
    with pytest.raises(ValueError):
        capture_body_overflow(env, max_body_tokens=-1, counter=_char_counter)


def test_capture_body_overflow_handle_total_matches_full_serialization():
    """`handle.total_tokens` MUST equal `counter(canonical_body_json)` so
    the wrapping driver can compute the recall delta without re-walking
    the source body."""
    import json
    from agency._envelope import ResponseEnvelope, capture_body_overflow
    body = {"chapters": [f"C{i}" * 50 for i in range(20)]}
    expected_total = _char_counter(
        json.dumps(body, sort_keys=True, separators=(",", ":")))
    env = ResponseEnvelope(prefix={"a": 1}, body=body)
    out = capture_body_overflow(env, max_body_tokens=200,
                                 counter=_char_counter)
    assert out.handle.total_tokens == expected_total
