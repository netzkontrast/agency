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


# ════════════════════════════════════════════════════════════════════════
# Spec 150 Slice 2 — LLM classifier path (via Spec 147 + Spec 279)
# ════════════════════════════════════════════════════════════════════════

class _FakeCapableDriver:
    """Stub anthropic driver — backend "anthropic" + scripted complete()."""

    def __init__(self, parsed: dict):
        self._parsed = parsed
        self.calls: list[dict] = []

    def backend(self) -> str:
        return "anthropic"

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        from agency._drivers._anthropic import Completion
        return Completion(
            text=__import__("json").dumps(self._parsed),
            stop_reason="end_turn",
            parsed=self._parsed,
            model="claude-test",
        )


def _seed_reflections(engine, iid):
    """Seed a mix of proposal-shaped + neutral reflections."""
    _call(engine, iid, "note", plan_slug="146-engine-output-prefix-discipline",
          observation="The agency_welcome response should add a "
                      "cache_control hint pointing at the prefix.")
    _call(engine, iid, "note", plan_slug="147-anthropic-driver-boundary",
          observation="Refine: typo in the boundary error mapping.")


def test_parse_amendment_uses_llm_when_capable_driver_wired(engine, iid):
    """Slice 2 invariant: with a capable AnthropicDriver, the verb calls
    `driver.complete(...)` with the structured-output schema and parses
    the LLM's proposals (NOT the keyword path)."""
    _seed_reflections(engine, iid)
    # Get the seeded reflection ids so the LLM stub can reference them.
    rows = engine.memory.g.query(
        "MATCH (r:Reflection) WHERE r.scope = $scope RETURN r",
        {"scope": "observation"})
    refls = [r["r"]["properties"] for r in rows]
    rid = refls[0].get("id") or ""
    spec_id = refls[0].get("plan_slug", "").split("-", 1)[0]
    fake_parsed = {"proposals": [{
        "reflection_id": rid,
        "spec_id": spec_id,
        "section": "Done When",
        "op": "add-done-when",
        "after": "Slice 2 — driver-derived classifier proposal text",
        "rationale": "LLM classifier promoted this reflection into a "
                     "concrete amendment over the keyword path (Spec 150 Slice 2).",
        "confidence": 0.92,
    }]}
    fake = _FakeCapableDriver(parsed=fake_parsed)
    engine.drivers.register("anthropic", fake)
    r = _call(engine, iid, "parse_amendment", scope="", limit=10)
    assert r.get("classifier") == "llm", (
        f"capable driver should drive the LLM classifier; got "
        f"classifier={r.get('classifier')!r}")
    assert len(r["proposals"]) == 1
    p = r["proposals"][0]
    assert p["spec_id"] == spec_id
    assert p["confidence"] == 0.92
    # And the driver was called exactly once with the schema.
    assert len(fake.calls) == 1
    assert fake.calls[0]["output_schema"]["properties"]["proposals"][
        "items"]["required"]


def test_parse_amendment_falls_back_to_keyword_when_driver_backend_none(
        engine, iid):
    """When the anthropic driver backend is "none" and we don't opt
    into delegation, the verb silently degrades to the keyword
    classifier — the documented Slice 2 fallback (existing tests
    keep passing without explicit opt-out)."""
    _seed_reflections(engine, iid)

    class _NoBackend:
        def backend(self) -> str:
            return "none"

    engine.drivers.register("anthropic", _NoBackend())
    r = _call(engine, iid, "parse_amendment", scope="", limit=10)
    # Falls back; some proposals classified by the keyword path.
    assert r.get("classifier") == "keyword"


def test_parse_amendment_emits_delegate_envelope_when_prefer_delegate(
        engine, iid):
    """Spec 279 integration: when `prefer_delegate=True` AND the driver
    backend is "none", the verb returns a `kind="llm_delegate"`
    envelope so the host (Claude Code) runs inference itself."""
    _seed_reflections(engine, iid)

    class _NoBackend:
        def backend(self) -> str:
            return "none"

    engine.drivers.register("anthropic", _NoBackend())
    r = _call(engine, iid, "parse_amendment", scope="", limit=10,
              prefer_delegate=True)
    assert r.get("classifier") == "llm-delegate"
    assert r.get("kind") == "llm_delegate"
    req = r.get("request") or {}
    assert req.get("kind") == "llm_delegate"
    assert "continuation_token" in req
    assert "messages" in req and isinstance(req["messages"], list)
    # The schema flows through to the envelope so Claude Code knows the
    # expected output shape.
    assert "output_schema" in req
    # Proposals empty until the host resumes with `host_completion`.
    assert r["proposals"] == []


def test_parse_amendment_resume_via_host_completion(engine, iid):
    """Spec 279 resume path: when `host_completion` is supplied, the
    verb parses the host's structured output into proposals — same
    shape as the driver path, classifier reports "host"."""
    _seed_reflections(engine, iid)
    rows = engine.memory.g.query(
        "MATCH (r:Reflection) WHERE r.scope = $scope RETURN r",
        {"scope": "observation"})
    refls = [r["r"]["properties"] for r in rows]
    rid = refls[0].get("id") or ""
    spec_id = refls[0].get("plan_slug", "").split("-", 1)[0]
    host_parsed = {"proposals": [{
        "reflection_id": rid,
        "spec_id": spec_id,
        "section": "Open questions",
        "op": "add-open-q",
        "after": "Should this hint live in the prefix or the body?",
        "rationale": "Host-LLM classified this as an open question "
                     "(Spec 279 resume path verified through dogfood).",
        "confidence": 0.85,
    }]}
    r = _call(engine, iid, "parse_amendment", scope="", limit=10,
              host_completion={"text": "<host-text>", "parsed": host_parsed})
    assert r.get("classifier") == "host"
    assert len(r["proposals"]) == 1
    assert r["proposals"][0]["confidence"] == 0.85


def test_parse_amendment_drops_proposals_for_hallucinated_reflection_ids(
        engine, iid):
    """Defense against hallucinated reflection_ids — if the LLM cites
    an id not in the input set, the proposal is dropped."""
    _seed_reflections(engine, iid)
    fake_parsed = {"proposals": [{
        "reflection_id": "ghost-id-does-not-exist",
        "spec_id": "146",
        "section": "Done When",
        "op": "add-done-when",
        "after": "Hallucinated proposal that should be filtered out",
        "rationale": "This is the hallucination defense test — the "
                     "classifier must drop proposals citing unknown ids.",
        "confidence": 0.5,
    }]}
    fake = _FakeCapableDriver(parsed=fake_parsed)
    engine.drivers.register("anthropic", fake)
    r = _call(engine, iid, "parse_amendment", scope="", limit=10)
    assert r["proposals"] == [], (
        f"hallucinated reflection_id must yield zero proposals; got "
        f"{r['proposals']!r}")


def test_parse_amendment_use_llm_false_skips_llm_path(engine, iid):
    """`use_llm=False` forces the keyword path even when a capable
    driver is wired — escape hatch for callers that want deterministic
    behavior or are running offline-by-policy."""
    _seed_reflections(engine, iid)
    fake = _FakeCapableDriver(parsed={"proposals": [
        {"reflection_id": "r1", "spec_id": "146", "section": "Done When",
         "op": "add-done-when", "after": "should not surface",
         "rationale": "This proposal must not be returned because use_llm "
                      "is False — the keyword path runs instead.",
         "confidence": 0.9}]})
    engine.drivers.register("anthropic", fake)
    r = _call(engine, iid, "parse_amendment", scope="", limit=10,
              use_llm=False)
    assert r.get("classifier") == "keyword"
    # And the driver was never called.
    assert fake.calls == []


def test_parse_amendment_driver_failure_falls_back_to_keyword(engine, iid):
    """Driver-side exceptions (auth / network / refusal) degrade
    gracefully to the keyword classifier rather than crashing the
    dogfood loop."""
    _seed_reflections(engine, iid)

    class _AngryDriver:
        def backend(self) -> str:
            return "anthropic"

        def complete(self, **_kwargs):
            raise RuntimeError("network: simulated outage")

    engine.drivers.register("anthropic", _AngryDriver())
    r = _call(engine, iid, "parse_amendment", scope="", limit=10)
    assert r.get("classifier") == "keyword", (
        f"driver failure should fall back to keyword; got "
        f"{r.get('classifier')!r}")


def test_parse_amendment_resume_malformed_raises():
    """Slice 2 boundary: a malformed `host_completion` (missing `text`)
    surfaces `HostDelegateError(MALFORMED)` through the verb — the
    classifier doesn't silently swallow protocol violations."""
    from agency._host_llm import HostDelegateError
    import tempfile as _tf
    eng = Engine(_tf.mktemp(suffix=".db"))
    intent_id = eng.intent.capture_and_confirm("x", "x", "x", owner="user")
    eng.registry.invoke(
        eng.memory, intent_id, "dogfood", "note",
        agent_id="agent:t",
        plan_slug="146-foo",
        observation="should add a thing")
    with pytest.raises(HostDelegateError) as exc:
        eng.registry.invoke(
            eng.memory, intent_id, "dogfood", "parse_amendment",
            agent_id="agent:t",
            host_completion={"parsed": {"proposals": []}})         # no `text`
    assert exc.value.code == HostDelegateError.MALFORMED


# ── Codex review on PR #136 round 2 — host/LLM proposal validation ────────
def test_parse_amendment_drops_proposals_with_invalid_op(engine, iid):
    """Codex review (P2): host_completion bypasses driver-side JSON
    schema, so the verb MUST validate enum-bound `op` itself."""
    _seed_reflections(engine, iid)
    rows = engine.memory.g.query(
        "MATCH (r:Reflection) WHERE r.scope = $scope RETURN r",
        {"scope": "observation"})
    rid = (rows[0]["r"]["properties"].get("id") or "")
    spec_id = rows[0]["r"]["properties"].get("plan_slug", "").split("-", 1)[0]
    host_parsed = {"proposals": [{
        "reflection_id": rid,
        "spec_id": spec_id,
        "section": "Done When",
        "op": "delete-everything",                                 # not in _LLM_OPS
        "after": "Should not pass",
        "rationale": "A malformed op must be dropped by the local "
                     "validator even when sent via host_completion.",
        "confidence": 0.9,
    }]}
    r = _call(engine, iid, "parse_amendment", scope="", limit=10,
              host_completion={"text": "<host-text>", "parsed": host_parsed})
    assert r["proposals"] == [], (
        f"invalid op must be dropped; got {r['proposals']!r}")


def test_parse_amendment_drops_proposals_with_invalid_section(engine, iid):
    """`section` must be in the documented enum set."""
    _seed_reflections(engine, iid)
    rows = engine.memory.g.query(
        "MATCH (r:Reflection) WHERE r.scope = $scope RETURN r",
        {"scope": "observation"})
    rid = (rows[0]["r"]["properties"].get("id") or "")
    spec_id = rows[0]["r"]["properties"].get("plan_slug", "").split("-", 1)[0]
    r = _call(engine, iid, "parse_amendment", scope="", limit=10,
              host_completion={"text": "<host-text>",
                                 "parsed": {"proposals": [{
                                     "reflection_id": rid,
                                     "spec_id": spec_id,
                                     "section": "Random Made Up Section",
                                     "op": "add-done-when",
                                     "after": "x",
                                     "rationale":
                                         "Rationale long enough to satisfy "
                                         "the 40-char floor for validation.",
                                     "confidence": 0.9}]}})
    assert r["proposals"] == []


def test_parse_amendment_drops_proposals_with_confidence_outside_unit_interval(
        engine, iid):
    """`confidence` must be in [0, 1]."""
    _seed_reflections(engine, iid)
    rows = engine.memory.g.query(
        "MATCH (r:Reflection) WHERE r.scope = $scope RETURN r",
        {"scope": "observation"})
    rid = (rows[0]["r"]["properties"].get("id") or "")
    spec_id = rows[0]["r"]["properties"].get("plan_slug", "").split("-", 1)[0]
    r = _call(engine, iid, "parse_amendment", scope="", limit=10,
              host_completion={"text": "<host-text>",
                                 "parsed": {"proposals": [{
                                     "reflection_id": rid,
                                     "spec_id": spec_id,
                                     "section": "Done When",
                                     "op": "add-done-when",
                                     "after": "x",
                                     "rationale":
                                         "Rationale long enough to satisfy "
                                         "the 40-char floor for validation.",
                                     "confidence": 5.0}]}})       # out of range
    assert r["proposals"] == []


def test_parse_amendment_drops_proposals_with_short_rationale(engine, iid):
    """`rationale` must meet the 40-char floor — symmetric with the
    `apply_amendment` AMENDMENT_VAGUE gate (Slice 1)."""
    _seed_reflections(engine, iid)
    rows = engine.memory.g.query(
        "MATCH (r:Reflection) WHERE r.scope = $scope RETURN r",
        {"scope": "observation"})
    rid = (rows[0]["r"]["properties"].get("id") or "")
    spec_id = rows[0]["r"]["properties"].get("plan_slug", "").split("-", 1)[0]
    r = _call(engine, iid, "parse_amendment", scope="", limit=10,
              host_completion={"text": "<host-text>",
                                 "parsed": {"proposals": [{
                                     "reflection_id": rid,
                                     "spec_id": spec_id,
                                     "section": "Done When",
                                     "op": "add-done-when",
                                     "after": "x",
                                     "rationale": "too short",     # < 40
                                     "confidence": 0.5}]}})
    assert r["proposals"] == []


def test_parse_amendment_overrides_spec_id_from_reflections_plan_slug(
        engine, iid):
    """Codex review (P2): even with a valid reflection_id, the model
    could return a spec_id that doesn't match the reflection's
    plan_slug — routing the amendment to the WRONG spec while
    provenance points elsewhere. The verb MUST derive spec_id from
    the cited reflection's plan_slug and drop mismatches."""
    _seed_reflections(engine, iid)
    rows = engine.memory.g.query(
        "MATCH (r:Reflection) WHERE r.scope = $scope RETURN r",
        {"scope": "observation"})
    # Pick the 146 reflection but have the model claim spec_id=999.
    refls = [r["r"]["properties"] for r in rows]
    refl_146 = next(r for r in refls
                    if r.get("plan_slug", "").startswith("146"))
    rid = refl_146.get("id") or ""
    fake_parsed = {"proposals": [{
        "reflection_id": rid,
        "spec_id": "999",                                          # mismatch!
        "section": "Done When",
        "op": "add-done-when",
        "after": "Mis-attributed amendment that should be dropped",
        "rationale": "Even with a valid reflection_id, a spec_id that "
                     "doesn't match the reflection's plan_slug must be "
                     "dropped — provenance integrity invariant.",
        "confidence": 0.8,
    }]}
    fake = _FakeCapableDriver(parsed=fake_parsed)
    engine.drivers.register("anthropic", fake)
    r = _call(engine, iid, "parse_amendment", scope="", limit=10)
    assert r["proposals"] == [], (
        f"spec_id mismatch must drop the proposal; got {r['proposals']!r}")


def test_parse_amendment_derives_spec_id_when_model_omits_it(engine, iid):
    """When the model leaves spec_id empty but supplies a valid
    reflection_id, the verb derives spec_id from the reflection's
    plan_slug — the slug is the ground-truth source."""
    _seed_reflections(engine, iid)
    rows = engine.memory.g.query(
        "MATCH (r:Reflection) WHERE r.scope = $scope RETURN r",
        {"scope": "observation"})
    refls = [r["r"]["properties"] for r in rows]
    refl_146 = next(r for r in refls
                    if r.get("plan_slug", "").startswith("146"))
    rid = refl_146.get("id") or ""
    fake_parsed = {"proposals": [{
        "reflection_id": rid,
        "spec_id": "",                                             # omitted!
        "section": "Done When",
        "op": "add-done-when",
        "after": "Derived-spec-id proposal text",
        "rationale": "The verb derives spec_id from the cited "
                     "reflection's plan_slug when the model omits it.",
        "confidence": 0.75,
    }]}
    fake = _FakeCapableDriver(parsed=fake_parsed)
    engine.drivers.register("anthropic", fake)
    r = _call(engine, iid, "parse_amendment", scope="", limit=10)
    assert len(r["proposals"]) == 1
    assert r["proposals"][0]["spec_id"] == "146"
