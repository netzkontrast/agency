"""Acceptance — the loop walk reducer (Spec 366 advance, looper run() on the spine).

advance() reads the machine state, runs the gate (criteria 364 + council verdict
365), consults control_evaluate, then moves via the lifecycle pillar (the sole
state writer). Status/stop_reason derive from the graph — no state.json in-session.
"""
from __future__ import annotations

import json
import os
import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine

scenarios("features/loop_advance.feature")

_REVISE = '{"verdict": "revise", "blocking_issues": ["same blocker"]}'


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


def _open(engine, *, max_revisions=3, no_progress_stall=2):
    from agency._loop import open_loop
    iid = engine.intent.capture("loop advance", "behaviour", "verified")
    engine.intent.confirm(iid)
    return open_loop(engine, iid, max_iterations=12, max_revisions=max_revisions,
                     no_progress_stall=no_progress_stall)["loop_id"]


@given("an open loop with a passing programmatic criterion", target_fixture="box")
def _open_prog(engine):
    from agency._loop import add_criterion
    lid = _open(engine)
    add_criterion(engine, lid, "programmatic", check=["true"], expect="exit_zero")
    return {"loop_id": lid}


@given("an open loop with a judge criterion", target_fixture="box")
def _open_judge(engine):
    from agency._loop import add_criterion
    lid = _open(engine)
    add_criterion(engine, lid, "judge", rubric="covers the goal")
    return {"loop_id": lid}


@given(parsers.parse("an open loop with a judge criterion and caps max_revisions {mr:d} stall {st:d}"),
       target_fixture="box")
def _open_caps(engine, mr, st):
    from agency._loop import add_criterion
    lid = _open(engine, max_revisions=mr, no_progress_stall=st)
    add_criterion(engine, lid, "judge", rubric="covers the goal")
    return {"loop_id": lid}


@when("I advance from planning to the plan gate")
def _adv_to_gate(engine, box):
    from agency._loop import advance
    box["last"] = advance(engine, box["loop_id"])


@when("I advance the clean plan gate")
def _adv_clean(engine, box):
    from agency._loop import advance
    box["last"] = advance(engine, box["loop_id"])


@when("I advance the plan gate with a revise verdict")
def _adv_revise(engine, box):
    from agency._loop import advance
    box["last"] = advance(engine, box["loop_id"], judge_output=_REVISE)


def _revise_cycles(engine, box, n):
    from agency._loop import advance
    for _ in range(n):
        if engine.memory.recall(box["loop_id"])["state"] == "planning":
            advance(engine, box["loop_id"])  # planning -> plan_gate
        box["last"] = advance(engine, box["loop_id"], judge_output=_REVISE)


@when(parsers.parse("the plan gate is revised {n:d} times"))
def _revise_n(engine, box, n):
    _revise_cycles(engine, box, n)


@when(parsers.parse("the plan gate is revised {n:d} times with the same blocker"))
def _revise_same(engine, box, n):
    _revise_cycles(engine, box, n)


@then(parsers.parse('the loop state is "{state}"'))
def _state(engine, box, state):
    assert engine.memory.recall(box["loop_id"])["state"] == state, box.get("last")


@then(parsers.parse("the revision count is {n:d}"))
def _rev_count(engine, box, n):
    prog = json.loads(engine.memory.recall(box["loop_id"]).get("progress") or "{}")
    assert prog.get("revisions") == n, prog


@then(parsers.parse('the loop failed with stop_reason "{reason}"'))
def _failed_stop(engine, box, reason):
    assert box["last"]["state"] == "failed", box["last"]
    assert box["last"].get("stop_reason") == reason, box["last"]


@then("the loop progress reads from the graph and no state.json was written")
def _graph_status(engine, box):
    prog = json.loads(engine.memory.recall(box["loop_id"]).get("progress") or "{}")
    assert prog.get("revisions", 0) >= 1, prog
    assert prog.get("stop_reason"), prog
    assert not os.path.exists("state.json")
