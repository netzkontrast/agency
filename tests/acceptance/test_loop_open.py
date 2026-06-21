"""Acceptance — opening a loop (Spec 366; _loop.open).

`agency/_loop.py::open` mints a Lifecycle on the "loop" machine via the pillar,
records the termination control on the node, and refuses a guard-free loop.
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine

scenarios("features/loop_open.feature")


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


@pytest.fixture
def confirmed_intent(engine):
    iid = engine.intent.capture("loop open", "behaviour", "verified")
    engine.intent.confirm(iid)
    return iid


@pytest.fixture
def box():
    return {}


@given("a fresh agency engine in code-mode", target_fixture="engine")
def _given_engine(engine):
    return engine


@given("a confirmed intent", target_fixture="confirmed_intent")
def _given_intent(confirmed_intent):
    return confirmed_intent


@when(parsers.parse("I open a loop with max_iterations {mi:d} and max_revisions {mr:d}"),
      target_fixture="box")
def _open(engine, confirmed_intent, mi, mr):
    from agency._loop import open_loop
    return {"result": open_loop(engine, confirmed_intent, max_iterations=mi, max_revisions=mr)}


@when("I open a guard-free loop", target_fixture="box")
def _open_guard_free(engine, confirmed_intent):
    from agency._loop import open_loop
    out = {}
    try:
        out["result"] = open_loop(engine, confirmed_intent, max_iterations=0,
                                  budget=None, no_progress_stall=0)
    except ValueError as exc:
        out["error"] = str(exc)
    return out


@then(parsers.parse('the loop state is "{state}"'))
def _state(engine, box, state):
    assert box["result"]["state"] == state, box["result"]


@then(parsers.parse("the recorded control has max_iterations {mi:d} and max_revisions {mr:d}"))
def _control(engine, box, mi, mr):
    import json
    node = engine.memory.recall(box["result"]["loop_id"])
    control = json.loads(node.get("loop_control") or "{}")
    assert control.get("max_iterations") == mi, control
    assert control.get("max_revisions") == mr, control


@then("opening is refused")
def _refused(box):
    assert "error" in box and "result" not in box, box
