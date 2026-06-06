"""Spec 018 Win 1 RED — `develop.skill_walk`: the atomic skill walker.

The boilerplate this replaces (the live measurement in the spec) is the
5× `SkillRun(...).submit(...)` pattern — open a run, submit each phase,
stop at the gate, resume. `skill_walk(name, inputs, resume_from="")`
collapses that into ONE call: walk the whole skill to the first hard
gate, returning the documented status contract.

Return shapes (the contract, Spec 018 §"Win 1"):
  - completed     → {status, skill_id, outputs}
  - input-required→ {status, phase, blocked_on, resume_with, skill_id, partial_outputs}
  - failed        → {status, phase, error, skill_id, completed_phases}
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        yield e
    finally:
        e.memory.close()


@pytest.fixture
def iid(engine):
    intent = engine.intent.capture(
        "walk a discipline atomically",
        "skill_walk runs to the first hard gate in one call",
        "the documented status contract holds",
    )
    engine.intent.confirm(intent)
    return intent


def _walk(engine, iid, name, inputs, resume_from=""):
    """Drive `develop.skill_walk` through the registry (the wire path)."""
    raw, _ = engine.registry.invoke(
        engine.memory, iid, "develop", "skill_walk",
        name=name, inputs=inputs, resume_from=resume_from,
    )
    return raw["result"] if isinstance(raw, dict) and "result" in raw else raw


# --- the core contract -----------------------------------------------------


def test_walk_stops_at_first_hard_gate(engine, iid):
    """`tdd` is red → green → refactor → verify(hard). A fresh walk runs the
    three plain phases then PAUSES at `verify`, returning the input-required
    contract: phase, blocked_on, resume_with, skill_id, partial_outputs."""
    res = _walk(engine, iid, "tdd", {
        "failing_test": "test_x asserts behaviour",
        "implementation": "def x(): ...",
        "refactored": "tidy",
        "tests_pass": "12 passed",
    })
    assert res["status"] == "input-required"
    assert res["phase"] == "verify"
    assert res["blocked_on"]                      # the blocked Gate id
    assert "tests_pass" in res["resume_with"]
    assert res["skill_id"]
    # the three completed phases' outputs flow into partial_outputs
    assert res["partial_outputs"].get("failing_test")


def test_resume_completes_the_walk(engine, iid):
    """Resuming with `resume_from=skill_id` confirms the paused gate and
    walks to completion — returning {status: completed, skill_id, outputs}."""
    paused = _walk(engine, iid, "tdd", {
        "failing_test": "t", "implementation": "i",
        "refactored": "r", "tests_pass": "ok",
    })
    skill_id = paused["skill_id"]
    done = _walk(engine, iid, "tdd",
                 {"tests_pass": "ok"}, resume_from=skill_id)
    assert done["status"] == "completed"
    assert done["skill_id"] == skill_id


def test_unknown_skill_is_a_failed_shape(engine, iid):
    """An unregistered skill name returns the failed contract (never a
    raw KeyError), listing the available skills so the caller can recover."""
    res = _walk(engine, iid, "no-such-skill", {})
    assert res["status"] == "failed"
    assert "no-such-skill" in res["error"]
    assert "tdd" in res.get("available", [])


def test_missing_required_produce_aborts_as_failed(engine, iid):
    """A plain phase whose required produce is absent aborts the walk with
    the failed contract — phase named, completed_phases listed. The walk
    does NOT leave a half-applied state past the failing phase."""
    res = _walk(engine, iid, "tdd", {"failing_test": "t"})  # no `implementation`
    assert res["status"] == "failed"
    assert res["phase"] == "green"
    assert res["completed_phases"] == ["red"]
    assert res["skill_id"]


# --- provenance: a walk IS an audit trail ----------------------------------


def test_walk_records_skill_serving_the_intent(engine, iid):
    """The walker opens a Skill run that SERVES the intent — the walk is
    provenance, reachable from the intent in one traversal."""
    res = _walk(engine, iid, "tdd", {
        "failing_test": "t", "implementation": "i",
        "refactored": "r", "tests_pass": "ok",
    })
    rows = engine.memory.g.query(
        "MATCH (s:Skill)-[:SERVES]->(i:Intent) WHERE i.id = $iid AND s.id = $sid RETURN s",
        {"iid": iid, "sid": res["skill_id"]},
    )
    assert len(rows) == 1


def test_pause_writes_blocked_gate_to_graph(engine, iid):
    """The pause is recorded: Skill -[:BLOCKED_ON]-> Gate{paused:true} — an
    auditor sees WHY the walk stopped (parallel to Codex C3)."""
    res = _walk(engine, iid, "tdd", {
        "failing_test": "t", "implementation": "i",
        "refactored": "r", "tests_pass": "ok",
    })
    rows = engine.memory.g.query(
        "MATCH (s:Skill)-[:BLOCKED_ON]->(g:Gate) WHERE s.id = $sid RETURN g",
        {"sid": res["skill_id"]},
    )
    assert len(rows) == 1
    assert rows[0]["g"]["properties"]["paused"] is True


def test_invoke_phase_executes_the_bound_verb(engine, iid, tmp_path):
    """`authoring-capabilities` phase 2 binds to develop.scaffold_capability.
    Walking it with a registry EXECUTES the verb (the file lands on disk),
    proving skill_walk drives the bound verbs, not just documents them. The
    later lint phase (phase 4) binds to plugin.lint_capability on a name that
    was never registered, so the walk ABORTS there with the failed contract —
    proving the walker surfaces a real phase-execution failure (not a raw
    exception)."""
    res = _walk(engine, iid, "authoring-capabilities", {
        "read_doctrine": "yes",
        "name": "walkcap", "kind": "light", "base_dir": str(tmp_path),
        "verbs_written": "yes",
        "budget_ok": "yes",
        "reflection_recorded": "rid",
    })
    assert (tmp_path / "walkcap.py").is_file(), "phase 2 must execute scaffold_capability"
    assert res["status"] == "failed"
    assert res["phase"] == "lint"
    assert "scaffold" in res["completed_phases"]
    assert res["skill_id"]
