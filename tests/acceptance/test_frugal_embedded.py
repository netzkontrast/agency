"""Acceptance — Frugal embedded in lifecycle (Spec 347).

Three depths: floor-gate invariant in resolve_machine, frugal stamp on every
transition event, and the 'frugal' drivable machine.
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, scenarios, then, when

from agency.engine import Engine
from agency._lifecycle_machines import register_machine, resolve_machine
from agency._frugal import frugal_level

scenarios("features/frugal_embedded.feature")


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


@pytest.fixture
def confirmed_intent(engine):
    iid = engine.intent.capture("frugal embedded", "behaviour", "verified")
    engine.intent.confirm(iid)
    return iid


@pytest.fixture
def lc_box():
    return {}


@given("a fresh agency engine in code-mode", target_fixture="engine")
def _given_engine(engine):
    return engine


@given("a confirmed intent", target_fixture="confirmed_intent")
def _given_intent(confirmed_intent):
    return confirmed_intent


# ── floor gate invariant ──────────────────────────────────────────────────────

@then('a machine whose path to "done" skips the floor gate raises')
def _floor_skip_raises():
    register_machine("skip-floor", {
        "initial": "start",
        "states": ["start", "gate", "done"],
        "transitions": {"start": ["done", "gate"], "gate": ["done"], "done": []},
        "terminal": ["done"],
        "floor_gates": ["gate"],
    })
    with pytest.raises(ValueError, match="floor"):
        resolve_machine("skip-floor")


@then('a machine whose path to "done" passes through the floor gate is accepted')
def _floor_honoured_loads():
    register_machine("honour-floor", {
        "initial": "start",
        "states": ["start", "gate", "done"],
        "transitions": {"start": ["gate"], "gate": ["done"], "done": []},
        "terminal": ["done"],
        "floor_gates": ["gate"],
    })
    m = resolve_machine("honour-floor")
    assert "gate" in m["floor_gates"]


# ── frugal stamp on transition events ────────────────────────────────────────

@when("I open an a2a lifecycle and move to \"completed\"", target_fixture="lc_box")
def _open_and_complete(engine, confirmed_intent):
    lc_id = engine.lifecycle.open(confirmed_intent)
    engine.lifecycle.move(lc_id, "working")
    engine.lifecycle.move(lc_id, "completed")
    return {"lc_id": lc_id}


@then("the durable transition event has a non-empty frugal field")
def _event_has_frugal(engine, lc_box):
    events = engine.memory.query_nodes("Event", {"lifecycle": lc_box["lc_id"],
                                                  "to_state": "completed"})
    assert events, "no durable Event found for the completed transition"
    assert events[0].get("frugal"), "frugal field missing or empty on transition Event"


# ── drivable frugal machine ───────────────────────────────────────────────────

@when('I open a lifecycle with machine "frugal"', target_fixture="lc_box")
def _open_frugal(engine, confirmed_intent):
    lc_id = engine.lifecycle.open(confirmed_intent, machine="frugal")
    return {"lc_id": lc_id}


@then('the opened lifecycle state is "assess"')
def _frugal_initial_state(engine, lc_box):
    assert engine.memory.recall(lc_box["lc_id"])["state"] == "assess"


@then("I can walk the frugal machine to \"done\"")
def _walk_frugal(engine, lc_box):
    lc = lc_box["lc_id"]
    engine.lifecycle.move(lc, "yagni")
    engine.lifecycle.move(lc, "implement")
    engine.lifecycle.move(lc, "floor-check")
    engine.lifecycle.move(lc, "done")
    assert engine.memory.recall(lc)["state"] == "done"


# ── single source for floor definition ───────────────────────────────────────

@then("the frugal field on the event matches frugal_level from Spec 332")
def _single_source(engine, lc_box):
    events = engine.memory.query_nodes("Event", {"lifecycle": lc_box["lc_id"],
                                                  "to_state": "completed"})
    assert events, "no durable Event found"
    assert events[0].get("frugal") == frugal_level()
