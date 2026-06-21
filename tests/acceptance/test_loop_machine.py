"""Acceptance — the loop machine (Spec 366, looper port on the lifecycle spine).

The looper port registers a "loop" state machine in machines.json (the Spec 345
data-seam). Its in-session runtime is this machine walked via the pillar
(ctx.lifecycle.open(machine="loop") / move) — no capability, just a machine.
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine
from agency._lifecycle_transitions import IllegalTransition

scenarios("features/loop_machine.feature")


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


@pytest.fixture
def confirmed_intent(engine):
    iid = engine.intent.capture("loop machine", "behaviour", "verified")
    engine.intent.confirm(iid)
    return iid


@pytest.fixture
def lc_box():
    return {}


# ── Given ────────────────────────────────────────────────────────────────────

@given("a fresh agency engine in code-mode", target_fixture="engine")
def _given_engine(engine):
    return engine


@given("a confirmed intent", target_fixture="confirmed_intent")
def _given_intent(confirmed_intent):
    return confirmed_intent


# ── When ─────────────────────────────────────────────────────────────────────

@when(parsers.parse('I open a "{machine}" lifecycle'), target_fixture="lc_box")
def _open(engine, confirmed_intent, machine):
    return {"lc_id": engine.lifecycle.open(confirmed_intent, machine=machine)}


@when(parsers.parse('I move it to "{to_state}"'))
def _move(engine, lc_box, to_state):
    engine.lifecycle.move(lc_box["lc_id"], to_state)


# ── Then ─────────────────────────────────────────────────────────────────────

@then(parsers.parse('its state is "{expected}"'))
def _state(engine, lc_box, expected):
    assert engine.memory.recall(lc_box["lc_id"]).get("state") == expected


@then(parsers.parse('moving it to "{to_state}" succeeds'))
def _move_ok(engine, lc_box, to_state):
    engine.lifecycle.move(lc_box["lc_id"], to_state)  # no exception = success


@then(parsers.parse('moving it to "{to_state}" raises IllegalTransition'))
def _move_raises(engine, lc_box, to_state):
    with pytest.raises(IllegalTransition):
        engine.lifecycle.move(lc_box["lc_id"], to_state)


@then(parsers.parse('the "{machine}" machine has terminals "{terminals}"'))
def _terminals(machine, terminals):
    from agency._lifecycle_machines import resolve_machine
    m = resolve_machine(machine)
    assert set(m.get("terminal", [])) == set(terminals.split(","))
