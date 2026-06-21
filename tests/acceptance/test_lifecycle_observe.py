"""Acceptance — the Lifecycle observe frame (Spec 341), REUSED on `manage`.

`read`/`watch` are thin projections (`manage.lifecycle` / `manage.lifecycle_trail`)
over the existing graph + the Spec 344 transition trail; `find` is
`manage.list("Lifecycle", where=)` and `check` is `gate.check` — both pure reuse.
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine
from conftest import invoke

scenarios("features/lifecycle_observe.feature")


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


@pytest.fixture
def confirmed_intent(engine):
    iid = engine.intent.capture("observe", "behaviour", "verified")
    engine.intent.confirm(iid)
    return iid


@given("a fresh agency engine in code-mode", target_fixture="engine")
def _given_engine(engine):
    return engine


@given("a confirmed intent", target_fixture="confirmed_intent")
def _given_intent(confirmed_intent):
    return confirmed_intent


@given('an opened lifecycle moved to "working"', target_fixture="lc")
def _open_working(engine, confirmed_intent):
    lc = engine.lifecycle.open(confirmed_intent)
    engine.lifecycle.move(lc, "working")
    return lc


@given('a "working" lifecycle and a "completed" lifecycle')
def _two_lifecycles(engine, confirmed_intent):
    lc1 = engine.lifecycle.open(confirmed_intent)
    engine.lifecycle.move(lc1, "working")
    lc2 = engine.lifecycle.open(confirmed_intent)
    engine.lifecycle.move(lc2, "working")
    engine.lifecycle.move(lc2, "completed")


@when("I read the lifecycle via manage.lifecycle", target_fixture="read_res")
def _read(engine, confirmed_intent, lc):
    res, _ = invoke(engine, confirmed_intent, "manage", "lifecycle", lifecycle_id=lc)
    return res


@then(parsers.parse('the read reports state "{state}" and the serving intent'))
def _read_reports(read_res, confirmed_intent, state):
    assert read_res.get("state") == state, read_res
    assert read_res.get("intent_id") == confirmed_intent, read_res


@when(parsers.parse('I list lifecycles in state "{state}"'), target_fixture="list_res")
def _list(engine, confirmed_intent, state):
    res, _ = invoke(engine, confirmed_intent, "manage", "list",
                    label="Lifecycle", where={"state": state})
    return res


@then(parsers.parse("exactly {n:d} lifecycle is returned"))
def _list_count(list_res, n):
    assert list_res.get("count") == n, list_res


@when("a gate fails on the lifecycle")
def _gate_fails(engine, confirmed_intent, lc):
    invoke(engine, confirmed_intent, "gate", "check",
           lifecycle_id=lc, name="spec-review", passed=False, evidence="nope")


@then(parsers.parse('the lifecycle read reports state "{state}"'))
def _read_state(engine, confirmed_intent, lc, state):
    res, _ = invoke(engine, confirmed_intent, "manage", "lifecycle", lifecycle_id=lc)
    assert res.get("state") == state, res


@when(parsers.parse('I move the lifecycle to "{to_state}"'))
def _move(engine, lc, to_state):
    engine.lifecycle.move(lc, to_state)


@when("I read the transition trail via manage.lifecycle_trail", target_fixture="trail_res")
def _trail(engine, confirmed_intent, lc):
    res, _ = invoke(engine, confirmed_intent, "manage", "lifecycle_trail", lifecycle_id=lc)
    return res


@then(parsers.parse('the trail contains a transition to "{state}"'))
def _trail_has(trail_res, state):
    tos = [t.get("to_state") for t in trail_res.get("transitions", [])]
    assert state in tos, trail_res
