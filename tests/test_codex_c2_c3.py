"""Codex review follow-on C2 + C3 (deferred from the 4e37470 batch).

C2 — `gate.check` accepts gates across amended intents:
    The original guard at gate.py:25 used `i.id = $iid` (exact match),
    which rejected the pre-amend lifecycle on amended-intent workflows.
    `memory.provenance` deliberately walks the SUPERSEDED_BY chain
    (memory.py:161-175); this guard now does the same.

C3 — `SkillRun.submit` persists hard-gate pauses:
    The original at skill.py:71-72 returned `input-required` but wrote
    no Gate / blocked-state to the graph. Auditors couldn't see WHY a
    run paused. The fix records a Gate{passed:False, paused:True} +
    BLOCKED_ON edge from the SkillRun to the Gate; the symmetric
    PASSED branch on confirmed resume keeps the bi-temporal trail
    complete on both halves of block → resume.
"""
import tempfile

import pytest

from agency.engine import Engine
from agency.skill import SkillRun


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


# ---------------------------------------------------------------------------
# C2 — gate.check across an amended intent chain.
# ---------------------------------------------------------------------------


def test_c2_gate_check_accepts_pre_amend_lifecycle(engine):
    """A lifecycle that SERVES the *original* intent should still pass the
    `lifecycle does not serve the current intent` guard when checked under
    the AMENDED intent — the SUPERSEDED_BY chain is the relation."""
    iid_original = engine.intent.capture(
        "ship something", "test green", "tests pass",
    )
    engine.intent.confirm(iid_original)

    # Lifecycle was opened under the original intent; SERVES = iid_original.
    lc = engine.memory.record("Lifecycle", {"state": "working", "phase": 0})
    engine.memory.link(lc, iid_original, "SERVES")

    # Amend the intent → new intent id, linked back via SUPERSEDED_BY.
    iid_amended = engine.intent.amend(iid_original, deliverable="test green (revised)")
    assert iid_amended != iid_original

    # gate.check is called under the AMENDED intent; the guard must
    # follow SUPERSEDED_BY back to the pre-amend lifecycle.
    raw, _ = engine.registry.invoke(
        engine.memory, iid_amended, "gate", "check",
        agent_id="agent:test",
        lifecycle_id=lc, name="acceptance", passed=True,
    )
    res = raw["result"]
    assert res["passed"] is True
    assert "gate" in res


def test_c2_gate_check_still_rejects_cross_intent_lifecycle(engine):
    """The guard is RELAXED for SUPERSEDED_BY but NOT for unrelated intents.
    A lifecycle serving a totally different intent must still be rejected."""
    iid_a = engine.intent.capture("intent A", "x", "y")
    engine.intent.confirm(iid_a)
    iid_b = engine.intent.capture("intent B", "x", "y")
    engine.intent.confirm(iid_b)

    lc_a = engine.memory.record("Lifecycle", {"state": "working", "phase": 0})
    engine.memory.link(lc_a, iid_a, "SERVES")

    raw, _ = engine.registry.invoke(
        engine.memory, iid_b, "gate", "check",
        agent_id="agent:test",
        lifecycle_id=lc_a, name="g", passed=True,
    )
    res = raw["result"]
    assert "error" in res
    assert "does not serve" in res["error"]


def test_c2_amend_chain_walks_in_both_directions(engine):
    """Whether the check happens under the OLDER or the NEWER intent, the
    SUPERSEDED_BY chain must be walked. memory._intent_chain walks both
    directions; this is the canonical test."""
    iid_v1 = engine.intent.capture("ship", "x", "y")
    engine.intent.confirm(iid_v1)
    iid_v2 = engine.intent.amend(iid_v1, deliverable="x revised")

    # Lifecycle SERVES the NEWER intent.
    lc = engine.memory.record("Lifecycle", {"state": "working", "phase": 0})
    engine.memory.link(lc, iid_v2, "SERVES")

    # Check via the OLDER intent — walk forward through SUPERSEDED_BY.
    raw, _ = engine.registry.invoke(
        engine.memory, iid_v1, "gate", "check",
        agent_id="agent:test",
        lifecycle_id=lc, name="acceptance", passed=True,
    )
    assert raw["result"]["passed"] is True


# ---------------------------------------------------------------------------
# C3 — SkillRun persists hard-gate pause + resume.
# ---------------------------------------------------------------------------


_SIMPLE_GATED_SKILL = {
    "name": "c3-fixture-skill",
    "kind": "discipline",
    "phases": [
        {"index": 1, "name": "do-work", "produces": ["work_result"]},
        {"index": 2, "name": "approve", "produces": ["sign_off"], "gate": "hard"},
    ],
}


@pytest.fixture
def iid(engine):
    intent = engine.intent.capture(
        "walk a gated skill",
        "hard-gate pause + resume both land in provenance",
        "blocked Gate + passed Gate appear as audit entries",
    )
    engine.intent.confirm(intent)
    return intent


def test_c3_pause_writes_blocked_gate_to_graph(engine, iid):
    run = SkillRun(engine.memory, iid, _SIMPLE_GATED_SKILL, registry=engine.registry)
    run.submit({"work_result": "done"})
    res = run.submit({"sign_off": "lgtm"})            # NOT confirmed -> pause
    assert res["status"] == "input-required"
    # The response now carries the blocked Gate id (was missing in v1).
    assert res["blocked_on"]

    # Graph: Skill -[:BLOCKED_ON]-> Gate{passed:False, paused:True}.
    rows = engine.memory.g.query(
        "MATCH (s:Skill)-[:BLOCKED_ON]->(g:Gate) "
        "WHERE s.name = $sn RETURN g",
        {"sn": "c3-fixture-skill"},
    )
    assert len(rows) == 1
    props = rows[0]["g"]["properties"]
    assert props["name"] == "approve"
    assert props["passed"] is False
    assert props["paused"] is True
    assert "awaiting confirmation" in props["evidence"]


def test_c3_blocked_gate_serves_intent_so_provenance_carries_it(engine, iid):
    """The blocked Gate node must SERVE the intent so the moat traversal
    (memory.provenance / cross-concern read) finds it."""
    run = SkillRun(engine.memory, iid, _SIMPLE_GATED_SKILL, registry=engine.registry)
    run.submit({"work_result": "done"})
    run.submit({"sign_off": "lgtm"})

    rows = engine.memory.g.query(
        "MATCH (g:Gate)-[:SERVES]->(i:Intent) "
        "WHERE i.id = $iid AND g.paused = true RETURN g",
        {"iid": iid},
    )
    assert len(rows) == 1


def test_c3_resume_writes_passed_gate_alongside_phase(engine, iid):
    """On confirmed resubmission, a symmetric Gate{passed:True} + PASSED
    edge is recorded so the resume is ALSO provenance. The block→resume
    cycle becomes an audit trail."""
    run = SkillRun(engine.memory, iid, _SIMPLE_GATED_SKILL, registry=engine.registry)
    run.submit({"work_result": "done"})
    run.submit({"sign_off": "lgtm"})                  # pause
    res = run.submit({"sign_off": "lgtm"}, confirmed=True)
    assert res["status"] == "completed"

    rows = engine.memory.g.query(
        "MATCH (s:Skill)-[:PASSED]->(g:Gate) "
        "WHERE s.name = $sn AND g.passed = true RETURN g",
        {"sn": "c3-fixture-skill"},
    )
    assert len(rows) == 1
    assert rows[0]["g"]["properties"]["paused"] is False


def test_c3_repeated_pause_each_writes_a_new_audit_gate(engine, iid):
    """Append-only graph: the user pausing twice produces TWO BLOCKED_ON
    Gate events. That's accurate provenance — repeated indecision is
    visible to auditors."""
    run = SkillRun(engine.memory, iid, _SIMPLE_GATED_SKILL, registry=engine.registry)
    run.submit({"work_result": "done"})
    run.submit({"sign_off": "v1"})
    run.submit({"sign_off": "v1"})                    # second pause
    run.submit({"sign_off": "v1"}, confirmed=True)

    rows = engine.memory.g.query(
        "MATCH (s:Skill)-[:BLOCKED_ON]->(g:Gate) "
        "WHERE s.name = $sn RETURN g",
        {"sn": "c3-fixture-skill"},
    )
    assert len(rows) == 2


def test_c3_non_gated_phase_does_not_emit_gate_node(engine, iid):
    """The fix only applies to phases with `gate: hard`. A document phase
    must still write only a Phase node, no Gate."""
    run = SkillRun(engine.memory, iid, _SIMPLE_GATED_SKILL, registry=engine.registry)
    run.submit({"work_result": "done"})               # phase 1 — no gate
    rows = engine.memory.g.query(
        "MATCH (g:Gate)-[:SERVES]->(i:Intent) "
        "WHERE i.id = $iid RETURN g",
        {"iid": iid},
    )
    assert len(rows) == 0
