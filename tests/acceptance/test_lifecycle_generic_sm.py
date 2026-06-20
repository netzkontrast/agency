"""Acceptance — Lifecycle generic state machine (Spec 345).

The lifecycle substrate accepts a named machine parameter; A2A is the default
(backward-compatible). Custom machines drive their own states and transitions;
derived machines (remote-async) inherit A2A with additive deltas; the ontology
widens to accept any registered machine's state.
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine
from agency._lifecycle_machines import register_machine
from agency._lifecycle_transitions import IllegalTransition

scenarios("features/lifecycle_generic_sm.feature")


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


@pytest.fixture
def confirmed_intent(engine):
    iid = engine.intent.capture("lifecycle generic sm", "behaviour", "verified")
    engine.intent.confirm(iid)
    return iid


@pytest.fixture
def lc_box():
    """Mutable carrier for the opened lifecycle id and any errors."""
    return {}


# ── Given ────────────────────────────────────────────────────────────────────

@given("a fresh agency engine in code-mode", target_fixture="engine")
def _given_engine(engine):
    return engine


@given("a confirmed intent", target_fixture="confirmed_intent")
def _given_intent(confirmed_intent):
    return confirmed_intent


@given(parsers.parse('a registered machine "{name}" with states {states_json} and initial "{initial}"'))
def _register_pipeline(name, states_json, initial):
    import json
    states = json.loads(states_json)
    # Build a minimal linear machine: initial→next→...→last (last is terminal)
    transitions = {}
    for i, s in enumerate(states):
        transitions[s] = [states[i + 1]] if i + 1 < len(states) else []
    register_machine(name, {
        "initial": initial,
        "states": states,
        "transitions": transitions,
    })


# ── When ─────────────────────────────────────────────────────────────────────

@when("I open a lifecycle with no machine specified", target_fixture="lc_box")
def _open_default(engine, confirmed_intent):
    lc_id = engine.lifecycle.open(confirmed_intent)
    return {"lc_id": lc_id}


@when(parsers.parse('I open a lifecycle with machine "{machine}"'), target_fixture="lc_box")
def _open_machine(engine, confirmed_intent, machine):
    lc_id = engine.lifecycle.open(confirmed_intent, machine=machine)
    return {"lc_id": lc_id}


# ── Then ─────────────────────────────────────────────────────────────────────

@then(parsers.parse('the opened lifecycle machine is "{expected}"'))
def _check_machine(engine, lc_box, expected):
    node = engine.memory.recall(lc_box["lc_id"])
    # a2a is the default; it is NOT stored on the node (byte-identical to pre-345)
    actual = node.get("machine", "a2a")
    assert actual == expected, actual


@then(parsers.parse('the opened lifecycle state is "{expected}"'))
def _check_state(engine, lc_box, expected):
    node = engine.memory.recall(lc_box["lc_id"])
    assert node.get("state") == expected, node.get("state")


@then(parsers.parse('moving "{machine}" lifecycle to "{to_state}" succeeds'))
def _move_succeeds(engine, lc_box, machine, to_state):
    engine.lifecycle.move(lc_box["lc_id"], to_state)


@then(parsers.parse('moving "{machine}" lifecycle to "{to_state}" from "{from_state}" raises IllegalTransition'))
def _move_raises(engine, confirmed_intent, machine, to_state, from_state):
    # Open a fresh lifecycle in the named machine, move to from_state, then
    # assert the next move raises IllegalTransition.
    lc_id = engine.lifecycle.open(confirmed_intent, machine=machine)
    if from_state != engine.memory.recall(lc_id).get("state"):
        engine.lifecycle.move(lc_id, from_state)
    with pytest.raises(IllegalTransition):
        engine.lifecycle.move(lc_id, to_state)


@then("resolving a machine with an orphaned terminal state raises")
def _floor_raises():
    from agency._lifecycle_machines import resolve_machine
    # A terminal state that has outgoing transitions violates the floor.
    register_machine("bad-floor", {
        "initial": "start",
        "states": ["start", "done"],
        "transitions": {"start": ["done"], "done": ["start"]},  # done is NOT terminal but has no outgoing-free state
        "terminal": ["done"],  # declared terminal but has outgoing edge → floor violation
    })
    with pytest.raises(ValueError, match="floor"):
        resolve_machine("bad-floor")


@then(parsers.parse('recording a Lifecycle with state "{state}" and machine "{machine}" passes ontology validation'))
def _ontology_accepts(state, machine):
    # Build a FRESH engine AFTER register_machine so _LIFECYCLE_ALL_STATES is widened.
    import tempfile
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        # record() enforces ontology — no ValueError = validation passed.
        lc_id = e.memory.record("Lifecycle", {"state": state, "phase": 0, "machine": machine})
        assert e.memory.recall(lc_id) is not None
        violations = e.ontology.violations("Lifecycle", {"state": state, "phase": 0})
        assert not violations, violations
    finally:
        e.memory.close()
