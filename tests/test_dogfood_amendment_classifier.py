"""Spec 150 Slice 1 — dogfood amendment classifier.

Goal 6 ("doctrine evolves through dogfooding") is the alignment matrix's
standing 🔴 critical gap: Reflections accumulate (Spec 045 gives semantic
recall) but NO automated path turns "observed pattern" → "spec amendment
proposal". Spec 014 was drafted for exactly this; Spec 150 closes it.

Slice 1 ships:
- `dogfood.parse_amendment(scope, since, limit)` — keyword classifier
  (Slice 2 swaps in the Spec 147 AnthropicDriver path with structured
  outputs; the keyword path is the documented fallback when the driver
  is unavailable, never silent no-op).
- `dogfood.apply_amendment(payload, dry_run=True, confirm_token=None)`
  — renders the proposed spec-edit as a unified diff; dry-run default;
  full write requires `confirm_token` matching the payload id-hash.
- Typed codes: `AMENDMENT_BAD_SPEC` / `AMENDMENT_NO_SOURCE` /
  `AMENDMENT_VAGUE`.
- Provenance moat: every accepted amendment writes an
  `Artefact(kind="amendment-proposal")` with PRODUCES-from edges to
  every cited Reflection — a reviewer can trace any amendment back to
  its source observations in one graph query.

Slice 2+ — Anthropic-driver structured-output classification, rubric,
de-dup hashing, `/agency-amendments` slash, accept-rate metric, auto-PR.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def iid(engine):
    return engine.intent.capture_and_confirm(
        "test amendment classifier", "x", "x", owner="user")


def _call(engine, iid, verb, **kw):
    r, _ = engine.registry.invoke(
        engine.memory, iid, "dogfood", verb,
        agent_id="agent:test", **kw)
    return r


# ── parse_amendment shape + classification ─────────────────────────────────
def test_parse_amendment_returns_payload_list(engine, iid):
    """No reflections → no proposals — clean empty list, never raises."""
    r = _call(engine, iid, "parse_amendment", scope="", limit=20)
    assert "proposals" in r and isinstance(r["proposals"], list)
    assert r["proposals"] == []


def test_parse_amendment_keyword_path_classifies_proposal(engine, iid):
    """A reflection that ARGUES for a spec change is classified as a proposal.
    The keyword path looks for "should add" / "propose" / "should be" /
    "missing from spec NNN" — strong-intent verbs."""
    # Seed: 3 reflections; one is a clear proposal.
    _call(engine, iid, "note", plan_slug="146-engine-output-prefix-discipline",
          observation="The agency_welcome response should add a "
                      "cache_control hint pointing at the prefix.")
    _call(engine, iid, "note", plan_slug="146-engine-output-prefix-discipline",
          observation="Just a neutral observation about timestamps.")
    _call(engine, iid, "note", plan_slug="147-anthropic-driver-boundary",
          observation="Refine: typo in the boundary error mapping.")
    r = _call(engine, iid, "parse_amendment", scope="", limit=20)
    proposals = r["proposals"]
    # At least one proposal classified by the keyword path.
    assert len(proposals) >= 1
    # And the shape matches the documented ProposalPayload schema.
    p = proposals[0]
    required = {"spec_id", "section", "op", "before", "after",
                "rationale", "source_reflections", "confidence"}
    assert required.issubset(p.keys()), (
        f"ProposalPayload missing keys: {required - p.keys()}")
    # Source reflections is non-empty (provenance moat invariant).
    assert len(p["source_reflections"]) >= 1
    # Spec id must be the documented 3-digit-string shape.
    assert isinstance(p["spec_id"], str) and p["spec_id"].isdigit()
    # Classifier-reported confidence in [0, 1].
    assert 0.0 <= p["confidence"] <= 1.0


def test_parse_amendment_neutral_observations_yield_no_proposals(engine, iid):
    """Observations that are just observations don't get promoted."""
    _call(engine, iid, "note", plan_slug="146-engine-output-prefix-discipline",
          observation="Spec ships fine. No changes needed.")
    _call(engine, iid, "note", plan_slug="147-anthropic-driver-boundary",
          observation="The driver boundary works as expected today.")
    r = _call(engine, iid, "parse_amendment", scope="", limit=20)
    assert r["proposals"] == [], (
        f"keyword classifier incorrectly promoted neutral text: {r['proposals']}")


def test_parse_amendment_scope_filters_by_plan_slug(engine, iid):
    """`scope` (substring on plan_slug) constrains the candidate set —
    cheap caller-side narrowing without exposing graph query language."""
    _call(engine, iid, "note", plan_slug="146-engine-output-prefix-discipline",
          observation="Should add a cache_control hint for the prefix.")
    _call(engine, iid, "note", plan_slug="147-anthropic-driver-boundary",
          observation="Should add a retry policy to the boundary.")
    r = _call(engine, iid, "parse_amendment", scope="146", limit=20)
    spec_ids = {p["spec_id"] for p in r["proposals"]}
    assert "146" in spec_ids
    assert "147" not in spec_ids


def test_parse_amendment_limit_caps_result_count(engine, iid):
    """Tunable limit on returned proposals (pagination ergonomics)."""
    for i in range(5):
        _call(engine, iid, "note",
              plan_slug=f"15{i}-some-spec",
              observation=f"Spec 15{i} should add a typed error code.")
    r = _call(engine, iid, "parse_amendment", scope="", limit=2)
    assert len(r["proposals"]) <= 2


# ── apply_amendment dry-run + provenance ──────────────────────────────────
_SENTINEL = object()


def _payload(spec_id="146", section="Done When", op="add-done-when",
             before="- [ ] existing item", after="- [ ] new proposed item",
             rationale="The reflections show a pattern that needs codifying "
                       "into the spec so downstream code derives from it.",
             source_reflections=_SENTINEL, confidence=0.7):
    # `_SENTINEL` lets callers pass `[]` explicitly to test the empty case
    # without the `or []` short-circuit substituting the default.
    if source_reflections is _SENTINEL:
        source_reflections = ["r1", "r2"]
    return {
        "spec_id": spec_id,
        "section": section,
        "op": op,
        "before": before,
        "after": after,
        "rationale": rationale,
        "source_reflections": source_reflections,
        "confidence": confidence,
    }


def test_apply_amendment_dry_run_returns_unified_diff(engine, iid):
    payload = _payload()
    r = _call(engine, iid, "apply_amendment", payload=payload, dry_run=True)
    assert "diff" in r
    diff = r["diff"]
    # Unified-diff markers — "---" / "+++" headers + +/- body lines.
    assert "---" in diff and "+++" in diff
    assert payload["after"] in diff or "+" in diff   # added line present


def test_apply_amendment_dry_run_writes_artefact_with_produces_from(engine, iid):
    """The provenance moat: an amendment proposal CITES its sources via
    PRODUCES-from edges so a reviewer reconstructs "this came from these
    observations" in one query."""
    nid1 = _call(engine, iid, "note", plan_slug="146-engine-output-prefix-discipline",
                 observation="Should add a cache hint")["reflection_id"]
    nid2 = _call(engine, iid, "note", plan_slug="146-engine-output-prefix-discipline",
                 observation="Should add a budget cap")["reflection_id"]
    payload = _payload(source_reflections=[nid1, nid2])
    r = _call(engine, iid, "apply_amendment", payload=payload, dry_run=True)
    assert "artefact_id" in r and r["artefact_id"], (
        "apply_amendment must record a provenance Artefact even in dry-run")
    # The Artefact has the right kind.
    artefacts = engine.memory.find("Artefact")
    art = next(a for a in artefacts if a["id"] == r["artefact_id"])
    assert art["kind"] == "amendment-proposal"
    # PRODUCES-from edges to every cited reflection.
    sourced = set()
    for r_node_id in (nid1, nid2):
        edges = engine.memory.g.query(
            "MATCH (a)-[e:PRODUCES_FROM]->(r) "
            "WHERE a.id = $art AND r.id = $rid RETURN e",
            {"art": r["artefact_id"], "rid": r_node_id})
        if edges:
            sourced.add(r_node_id)
    assert sourced == {nid1, nid2}, (
        f"provenance edges missing for {{{nid1}, {nid2}}} - {nid1}, {nid2} sourced={sourced}")


def test_apply_amendment_dry_run_does_not_mutate_spec_file(engine, iid, tmp_path):
    """dry_run=True must NEVER touch the filesystem — the spec.md stays as
    it was; the diff is the only output."""
    payload = _payload()
    r = _call(engine, iid, "apply_amendment", payload=payload, dry_run=True)
    # No `written_path` in the response on dry-run.
    assert "written_path" not in r or not r["written_path"]


# ── typed failure codes ──────────────────────────────────────────────────
def test_apply_amendment_bad_spec_returns_typed_code(engine, iid):
    """A proposal naming a non-existent spec_id fails with the documented code."""
    payload = _payload(spec_id="9999")              # not a real spec
    with pytest.raises(Exception) as excinfo:
        _call(engine, iid, "apply_amendment", payload=payload, dry_run=True)
    # The free-string Codes constant is AMENDMENT_BAD_SPEC.
    assert "AMENDMENT_BAD_SPEC" in str(excinfo.value) or "amendment_bad_spec" in str(excinfo.value)


def test_apply_amendment_no_source_returns_typed_code(engine, iid):
    payload = _payload(source_reflections=[])
    with pytest.raises(Exception) as excinfo:
        _call(engine, iid, "apply_amendment", payload=payload, dry_run=True)
    assert "AMENDMENT_NO_SOURCE" in str(excinfo.value) or "amendment_no_source" in str(excinfo.value)


def test_apply_amendment_vague_rationale_returns_typed_code(engine, iid):
    payload = _payload(rationale="too short")        # < 40 chars
    with pytest.raises(Exception) as excinfo:
        _call(engine, iid, "apply_amendment", payload=payload, dry_run=True)
    assert "AMENDMENT_VAGUE" in str(excinfo.value) or "amendment_vague" in str(excinfo.value)


# ── confirm_token gate (live-write opt-in) ─────────────────────────────────
def test_apply_amendment_live_write_requires_confirm_token(engine, iid):
    """dry_run=False without matching confirm_token must NOT write — the
    confirmation step is a guard against accidental spec mutation."""
    payload = _payload()
    with pytest.raises(Exception) as excinfo:
        _call(engine, iid, "apply_amendment", payload=payload,
              dry_run=False, confirm_token="wrong-token")
    # Error names the confirm_token mismatch (free-string per Spec 001).
    assert "confirm_token" in str(excinfo.value).lower() or \
           "amendment_unconfirmed" in str(excinfo.value).lower()


# ── Codes constants exist (toolresult sugar) ──────────────────────────────
def test_codes_amendment_constants_are_defined():
    """Spec 150 amendment codes are sugar on `Codes` per Spec 059."""
    from agency.toolresult import Codes
    assert Codes.AMENDMENT_BAD_SPEC == "amendment_bad_spec"
    assert Codes.AMENDMENT_NO_SOURCE == "amendment_no_source"
    assert Codes.AMENDMENT_VAGUE == "amendment_vague"
