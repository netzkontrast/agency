"""Acceptance — develop.maintain: the autolearning recurring-maintenance loop.

Behaviour under test:
  - maintain returns the hardened seven-phase steward discipline (the loop lives
    in code, not a fragile external prompt) + live-graph signals + a recorded
    MaintenanceRun;
  - across runs it learns: the new run links PRECEDES from the prior one (the run
    chain is the loop's memory) and reports the prior run.
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import scenarios, then, when, given

from agency.engine import Engine

from conftest import invoke

scenarios("features/develop_maintain.feature")


@pytest.fixture
def ctx():
    return {}


@pytest.fixture
def engine():
    eng = Engine(tempfile.mktemp(suffix=".db"))
    yield eng
    eng.memory.close()


@pytest.fixture
def confirmed_intent(engine):
    iid = engine.intent.capture("maintain", "steward loop", "phases returned")
    engine.intent.confirm(iid)
    return iid


@given("a fresh agency engine")
def _fresh(engine):
    return engine


@given("a confirmed intent")
def _intent(confirmed_intent, ctx):
    ctx["iid"] = confirmed_intent


def _res(r):
    return r["result"] if isinstance(r, dict) and "result" in r else r


@when("I invoke develop maintain")
def _maintain(engine, ctx):
    r, _ = invoke(engine, ctx["iid"], "develop", "maintain")
    ctx["out"] = _res(r)


@when("I invoke develop maintain twice")
def _maintain_twice(engine, ctx):
    r1, _ = invoke(engine, ctx["iid"], "develop", "maintain")
    r2, _ = invoke(engine, ctx["iid"], "develop", "maintain")
    ctx["first"], ctx["second"] = _res(r1), _res(r2)


@then("maintain returns the seven steward phases")
def _phases(ctx):
    phases = ctx["out"]["phases"]
    assert isinstance(phases, list) and len(phases) == 7


@then("maintain returns live-graph signals")
def _signals(ctx):
    sig = ctx["out"]["signals"]
    assert "intents" in sig and "observation_backlog" in sig
    assert sig["intents"] >= 1               # the confirmed intent is live


@then("maintain records a maintenance run")
def _recorded(engine, ctx):
    rid = ctx["out"]["run_id"]
    assert rid is not None
    assert engine.memory.recall_typed(rid, "MaintenanceRun") is not None


@then("the second run links PRECEDES from the first")
def _chain(engine, ctx):
    first_id = ctx["first"]["run_id"]
    second_id = ctx["second"]["run_id"]
    rows = engine.memory.g.query(
        "MATCH (a:MaintenanceRun)-[:PRECEDES]->(b:MaintenanceRun) "
        "WHERE a.id = $a AND b.id = $b RETURN a.id AS x",
        {"a": first_id, "b": second_id})
    assert len(rows) == 1


@then("the second run reports the first as its prior")
def _prior(ctx):
    assert ctx["second"]["prior"]["id"] == ctx["first"]["run_id"]
