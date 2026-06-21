"""Acceptance — the loop-design wizard (Spec 367, looper's interview as a skill).

The 7-stage interview is a walkable skill registered into the develop ontology
(no new capability). It walks one phase at a time (progressive disclosure); the
council + control phases are hard gates (the two invariants); phase 6 renders a
graph-derived ASCII preview. The walk records a SkillRun provenance trail.
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine

scenarios("features/loop_wizard.feature")

_PRODUCES = {
    "goal": {"goal_id": "i-1"},
    "verification": {"criteria": "set"},
    "host": {"host": "claude"},
    "council": {"council": "ok"},
    "control": {"loop_id": "lc-1"},
    "confirm": {"preview_ok": "yes"},
    "emit": {"emitted": "yes"},
}


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


@pytest.fixture
def box():
    return {}


@given("a fresh agency engine in code-mode", target_fixture="engine")
def _eng(engine):
    return engine


def _open(engine):
    from agency._loop import open_loop
    iid = engine.intent.capture("loop design", "a loop", "designed")
    engine.intent.confirm(iid)
    return iid, open_loop(engine, iid, max_iterations=5)["loop_id"]


@given("an open loop with only a reviewer member", target_fixture="box")
def _open_reviewer(engine):
    from agency._loop import add_member
    _iid, lid = _open(engine)
    add_member(engine, lid, "reviewer", scope="plan")
    return {"loop_id": lid}


@given("an open loop with a programmatic criterion and a judge member", target_fixture="box")
def _open_full(engine):
    from agency._loop import add_criterion, add_member
    _iid, lid = _open(engine)
    add_criterion(engine, lid, "programmatic", check=["true"], expect="exit_zero")
    add_member(engine, lid, "judge", scope="both", family="codex")
    return {"loop_id": lid}


# ── registration + progressive disclosure ────────────────────────────────────
@then(parsers.parse('the engine ontology exposes the "{name}" skill'))
def _ont_skill(engine, name):
    assert engine.ontology.skill(name)["name"] == name


@when("I start walking the loop-design skill", target_fixture="box")
def _start_walk(engine):
    from agency.skill import SkillRun
    from agency._loop import LOOP_DESIGN_SKILL
    iid = engine.intent.capture("loop design", "a loop", "designed")
    engine.intent.confirm(iid)
    return {"run": SkillRun(engine.memory, iid, LOOP_DESIGN_SKILL), "iid": iid}


@then(parsers.parse('the walker offers phase {idx:d} "{name}" only'))
def _phase_only(box, idx, name):
    cur = box["run"].current()
    assert cur["index"] == idx and cur["name"] == name, cur


@then(parsers.parse('advancing offers phase {idx:d} "{name}"'))
def _advance_phase(box, idx, name):
    box["run"].submit(_PRODUCES["goal"])
    cur = box["run"].current()
    assert cur["index"] == idx and cur["name"] == name, cur


# ── hard-gate structure ──────────────────────────────────────────────────────
@then(parsers.parse('the loop-design "{phase_name}" phase is a hard gate'))
def _phase_hard(phase_name):
    from agency._loop import LOOP_DESIGN_SKILL
    p = next(p for p in LOOP_DESIGN_SKILL["phases"] if p["name"] == phase_name)
    assert p.get("gate") == "hard", p


# ── reviewer-only rule (council gate predicate) ──────────────────────────────
@then("a verdict source is not present for the loop")
def _no_verdict(engine, box):
    from agency._loop import verdict_source_present
    assert verdict_source_present(engine, box["loop_id"]) is False


@when("I add a judge member to the loop")
def _add_judge(engine, box):
    from agency._loop import add_member
    add_member(engine, box["loop_id"], "judge", scope="both", family="codex")


@then("a verdict source is present for the loop")
def _has_verdict(engine, box):
    from agency._loop import verdict_source_present
    assert verdict_source_present(engine, box["loop_id"]) is True


# ── termination guard (control gate predicate) ───────────────────────────────
@then("a control with no caps has no termination guard")
def _no_guard():
    from agency._loop import termination_guard_present
    assert termination_guard_present({"max_iterations": 0}) is False


@then("a control with max_iterations has a termination guard")
def _has_guard():
    from agency._loop import termination_guard_present
    assert termination_guard_present({"max_iterations": 12}) is True


# ── graph-derived preview ────────────────────────────────────────────────────
@when("I render the loop preview", target_fixture="box")
def _render_preview(engine, box):
    from agency._loop import preview
    box["preview"] = preview(engine, box["loop_id"])
    return box


@then("the preview shows the loop flow, the criteria, the council, and the stops")
def _check_preview(box):
    a = box["preview"]["ascii"]
    assert "planning" in a and "delivery_gate" in a, a
    assert "criteria (1)" in a, a
    assert "council (1)" in a, a
    assert "stops:" in a and "max_iterations" in a, a


# ── SkillRun provenance ──────────────────────────────────────────────────────
@when("I walk the loop-design skill to completion", target_fixture="box")
def _walk_complete(engine):
    from agency.skill import SkillRun
    from agency._loop import LOOP_DESIGN_SKILL
    iid = engine.intent.capture("loop design", "a loop", "designed")
    engine.intent.confirm(iid)
    run = SkillRun(engine.memory, iid, LOOP_DESIGN_SKILL)
    while not run.done:
        cur = run.current()
        run.submit(_PRODUCES[cur["name"]], confirmed=(cur.get("gate") == "hard"))
    return {"iid": iid}


@then(parsers.parse('a Skill named "{name}" serves the intent with seven phase records'))
def _skill_serves(engine, box, name):
    served = engine.memory.g.query(
        "MATCH (s:Skill)-[:SERVES]->(i:Intent) WHERE s.name=$n AND i.id=$iid RETURN s",
        {"n": name, "iid": box["iid"]})
    assert served, "Skill does not SERVE the intent"
    phases = engine.memory.g.query(
        "MATCH (s:Skill)-[:HAS_PHASE]->(p:Phase) WHERE s.name=$n RETURN p", {"n": name})
    assert len(phases) == 7, f"expected 7 phase records, got {len(phases)}"
