"""Acceptance — Lifecycle pillar substrate (Spec 339).

Behaviour of the hardened `agency/lifecycle.py` substrate write frame:
`open` mints `submitted`, `move` is the sole state-shaped writer that validates
the target state + refuses a no-op, `close` drives to a terminal state. The
transition table (340), events (344), and parameterization (342) land later.
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine
from agency._substrate_tools import LifecycleOpen, LifecycleMove
from conftest import invoke

scenarios("features/lifecycle.feature")


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


@pytest.fixture
def confirmed_intent(engine):
    iid = engine.intent.capture("lifecycle acceptance", "behaviour", "verified")
    engine.intent.confirm(iid)
    return iid


@pytest.fixture
def box():
    """Mutable carrier for cross-step error capture."""
    return {}


@given("a fresh agency engine in code-mode", target_fixture="engine")
def _given_engine(engine):
    return engine


@given("a confirmed intent", target_fixture="confirmed_intent")
def _given_intent(confirmed_intent):
    return confirmed_intent


@when("I open a lifecycle serving the intent", target_fixture="lc")
def _open_when(engine, confirmed_intent):
    return engine.lifecycle.open(confirmed_intent)


@given("an opened lifecycle", target_fixture="lc")
def _open_given(engine, confirmed_intent):
    return engine.lifecycle.open(confirmed_intent)


@when(parsers.parse('I move the lifecycle to "{to_state}"'))
def _move(engine, lc, to_state, box):
    try:
        engine.lifecycle.move(lc, to_state)
        box["error"] = None
    except Exception as exc:  # noqa: BLE001
        box["error"] = exc


@when(parsers.parse('I move the lifecycle to "{to_state}" again'))
def _move_again(engine, lc, to_state, box):
    try:
        engine.lifecycle.move(lc, to_state)
        box["second_error"] = None
    except Exception as exc:  # noqa: BLE001
        box["second_error"] = exc


@when("I move the lifecycle to an unknown state")
def _move_unknown(engine, lc, box):
    try:
        engine.lifecycle.move(lc, "bogus-state")
        box["error"] = None
    except Exception as exc:  # noqa: BLE001
        box["error"] = exc


@when(parsers.parse('I close the lifecycle as "{outcome}"'))
def _close(engine, lc, outcome):
    engine.lifecycle.close(lc, outcome=outcome)


@then(parsers.parse('the opened lifecycle state is "{expected}"'))
def _check_state(engine, lc, expected):
    assert engine.memory.recall(lc).get("state") == expected


@then("the move is rejected")
def _move_rejected(box):
    assert box.get("error") is not None


@then("the second move is rejected")
def _second_rejected(box):
    assert box.get("second_error") is not None


# ── Spec 339a-cont — ctx.lifecycle + lifecycle_* substrate tools + delegate ───


@when("I open a remote-async lifecycle serving the intent", target_fixture="lc")
def _open_param(engine, confirmed_intent):
    return engine.lifecycle.open(confirmed_intent, parameterization="remote-async")


@then(parsers.parse('the opened lifecycle parameterization is "{expected}"'))
def _check_param(engine, lc, expected):
    assert engine.memory.recall(lc).get("parameterization") == expected


@given("an opened lifecycle via the lifecycle_open substrate tool", target_fixture="lc")
def _open_via_substrate(engine, confirmed_intent):
    lifecycle_open = LifecycleOpen().bind(engine)
    return lifecycle_open(confirmed_intent)["lifecycle_id"]


@when(parsers.parse('I move the lifecycle to "{to_state}" via the lifecycle_move substrate tool'))
def _move_via_substrate(engine, lc, to_state):
    lifecycle_move = LifecycleMove().bind(engine)
    lifecycle_move(lc, to_state)


@when("delegate fans out one item", target_fixture="lc")
def _fan_out_one(engine, confirmed_intent):
    res, _ = invoke(engine, confirmed_intent, "delegate", "fan_out",
                    driver="reflect", driver_verb="note",
                    items=[{"scope": "observation", "text": "x"}], quota=1)
    result = res.get("result", res) if isinstance(res, dict) else res
    return result["children"][0]["lifecycle"]


@then(parsers.parse('the child lifecycle parameterization is "{expected}"'))
def _child_param(engine, lc, expected):
    assert engine.memory.recall(lc).get("parameterization") == expected


@then(parsers.parse('the child lifecycle state is "{expected}"'))
def _child_state(engine, lc, expected):
    assert engine.memory.recall(lc).get("state") == expected


# ── Spec 344 — lifecycle transition events (the event bus) ────────────────────


def _transition_events(engine):
    return [e for e in engine.memory.find("Event")
            if e.get("name") == "lifecycle_transition"]


def _monitor_events(engine):
    import json
    import os
    p = engine.monitor.path
    if not os.path.exists(p):
        return []
    return [json.loads(line) for line in open(p).read().splitlines() if line]


@when("a gate fails on the lifecycle")
def _gate_fails(engine, confirmed_intent, lc):
    invoke(engine, confirmed_intent, "gate", "check",
           lifecycle_id=lc, name="probe", passed=False, evidence="nope")


@then("no lifecycle_transition Event exists in the graph")
def _no_transition_event(engine):
    assert _transition_events(engine) == []


@then("a lifecycle transition MonitorEvent was emitted")
def _monitor_emitted(engine):
    hits = [e for e in _monitor_events(engine)
            if e.get("source") == "lifecycle" and e.get("kind") == "transition"]
    assert hits, "expected a lifecycle/transition MonitorEvent on the channel"


@then(parsers.parse('a lifecycle_transition Event to "{state}" exists in the graph'))
def _transition_event_to(engine, state):
    matches = [e for e in _transition_events(engine) if e.get("to_state") == state]
    assert matches, f"no lifecycle_transition Event with to_state={state!r}"


@then("that Event is OBSERVED_DURING the intent and the lifecycle")
def _event_observed_during(engine, confirmed_intent, lc):
    ev = _transition_events(engine)[0]
    observed = {n.get("id") for n in
                engine.memory.neighbors(ev["id"], "OBSERVED_DURING", direction="out")}
    assert confirmed_intent in observed, observed
    assert lc in observed, observed


@then(parsers.parse("the durable transition trail has {n:d} events"))
def _trail_count(engine, lc, n):
    trail = [e for e in engine.memory.neighbors(lc, "OBSERVED_DURING", direction="in")
             if e.get("name") == "lifecycle_transition"]
    assert len(trail) == n, f"expected {n} durable transitions, got {len(trail)}"


@then("a lifecycle_transition event appears in manage.timeline for the intent")
def _timeline_has_transition(engine, confirmed_intent):
    res, _ = invoke(engine, confirmed_intent, "manage", "timeline",
                    for_intent_id=confirmed_intent)
    names = [item.get("name") for item in res.get("timeline", [])]
    assert "lifecycle_transition" in names, names


# ── Spec 340 — the enforced A2A transition table ──────────────────────────────


@when(parsers.parse('I move the lifecycle to "{to_state}" expecting an illegal transition'))
def _move_illegal(engine, lc, to_state, box):
    try:
        engine.lifecycle.move(lc, to_state)
        box["illegal"] = None
    except Exception as exc:  # noqa: BLE001
        box["illegal"] = exc


@then(parsers.parse('the move is rejected as an illegal transition with allowed "{allowed}"'))
def _rejected_illegal_allowed(box, allowed):
    from agency._lifecycle_transitions import IllegalTransition
    err = box.get("illegal")
    assert isinstance(err, IllegalTransition), err
    assert str(err.allowed) == allowed, err.allowed


@then("the move is rejected as an illegal transition")
def _rejected_illegal(box):
    from agency._lifecycle_transitions import IllegalTransition
    assert isinstance(box.get("illegal"), IllegalTransition), box.get("illegal")


@then("every state in the transition table is a valid lifecycle state")
def _table_consistent():
    from agency._lifecycle_transitions import load_base_table
    from agency.ontology import LIFECYCLE_STATES
    table = load_base_table()
    for state, targets in table.items():
        assert state in LIFECYCLE_STATES, state
        for target in targets:
            assert target in LIFECYCLE_STATES, target


@given(parsers.parse('a transition-table override adding "{src}" to "{dst}"'))
def _override(engine, confirmed_intent, src, dst):
    import json
    from agency.lifecycle import TRANSITION_TABLE_KIND, TRANSITION_TABLE_NODE_ID
    # Stored at the deterministic id so `move` reads it via an O(1) recall
    # (Spec 340 perf fix) — not a full Artefact scan.
    aid = engine.memory.record("Artefact", {"kind": TRANSITION_TABLE_KIND,
                                            "table": json.dumps({src: [dst]})},
                               node_id=TRANSITION_TABLE_NODE_ID)
    engine.memory.link(aid, confirmed_intent, "SERVES")
    return aid


@when(parsers.parse('I move an opened lifecycle to "{to_state}"'), target_fixture="lc")
def _open_and_move(engine, confirmed_intent, to_state):
    lc = engine.lifecycle.open(confirmed_intent)
    engine.lifecycle.move(lc, to_state)
    return lc


@then("loading the effective table is rejected")
def _effective_rejected(engine):
    from agency._lifecycle_transitions import IllegalTransition
    with pytest.raises(IllegalTransition):
        engine.lifecycle._effective_table()


# ── Spec 349b — lifecycle transitions on the pillar event bus ─────────────────


@given("a subscriber registered for the lifecycle transition event",
       target_fixture="bus_box")
def _register_bus_subscriber():
    from agency import _events
    from agency.lifecycle import LIFECYCLE_TRANSITION_EVENT
    received: list[dict] = []

    def _capture(engine, event):
        received.append(event)
        return ""

    # Unique name so this test subscription doesn't collide with the built-in
    # `lifecycle.monitor` one; idempotent re-registration is safe.
    _events.subscribe(LIFECYCLE_TRANSITION_EVENT, _capture,
                      name="test.capture_transition")
    return {"received": received}


@then(parsers.parse('the subscriber received a transition to "{to_state}"'))
def _subscriber_received(bus_box, to_state):
    tos = [e.get("to_state") for e in bus_box["received"]]
    assert to_state in tos, tos


# ── Spec 341 — observe suite: read · find · check · watch ────────────────────


@then(parsers.parse('lifecycle.read returns the state "{expected}"'))
def _read_state(engine, lc, expected):
    result = engine.lifecycle.read(lc)
    assert result.get("state") == expected, result


@then("lifecycle.read includes the serving intent_id")
def _read_intent(engine, lc, confirmed_intent):
    result = engine.lifecycle.read(lc)
    assert result.get("intent_id") == confirmed_intent, result


@then(parsers.parse("lifecycle.find for the intent returns {n:d} lifecycle"))
@then(parsers.parse("lifecycle.find for the intent returns {n:d} lifecycles"))
def _find_for_intent(engine, confirmed_intent, n):
    found = engine.lifecycle.find(confirmed_intent)
    assert len(found) == n, found


@then(parsers.parse('lifecycle.find for the intent in state "{state}" returns {n:d} lifecycle'))
@then(parsers.parse('lifecycle.find for the intent in state "{state}" returns {n:d} lifecycles'))
def _find_filtered(engine, confirmed_intent, state, n):
    found = engine.lifecycle.find(confirmed_intent, state=state)
    assert len(found) == n, found


@then(parsers.parse('lifecycle.check for "{state}" is true'))
def _check_true(engine, lc, state):
    assert engine.lifecycle.check(lc, state) is True


@then(parsers.parse('lifecycle.check for "{state}" is false'))
def _check_false(engine, lc, state):
    assert engine.lifecycle.check(lc, state) is False


@then(parsers.parse("lifecycle.watch returns {n:d} transition event"))
@then(parsers.parse("lifecycle.watch returns {n:d} transition events"))
def _watch_count(engine, lc, n):
    trail = engine.lifecycle.watch(lc)
    assert len(trail) == n, trail


@then(parsers.parse('the first watch event is a transition to "{state}"'))
def _watch_first(engine, lc, state):
    trail = engine.lifecycle.watch(lc)
    assert trail, "watch trail is empty"
    assert trail[0].get("to_state") == state, trail[0]


# ── Spec 341 — substrate tools ────────────────────────────────────────────────


@then(parsers.parse('the lifecycle_read substrate tool returns state "{expected}"'))
def _substrate_read(engine, lc, expected):
    from agency._substrate_tools import LifecycleRead
    result = LifecycleRead().bind(engine)(lc)
    assert result.get("state") == expected, result


@then(parsers.parse("the lifecycle_find substrate tool returns {n:d} lifecycle for the intent"))
@then(parsers.parse("the lifecycle_find substrate tool returns {n:d} lifecycles for the intent"))
def _substrate_find(engine, confirmed_intent, n):
    from agency._substrate_tools import LifecycleFind
    result = LifecycleFind().bind(engine)(confirmed_intent)
    assert len(result.get("lifecycles", [])) == n, result


@then(parsers.parse("the lifecycle_watch substrate tool returns {n:d} transition event"))
@then(parsers.parse("the lifecycle_watch substrate tool returns {n:d} transition events"))
def _substrate_watch(engine, lc, n):
    from agency._substrate_tools import LifecycleWatch
    result = LifecycleWatch().bind(engine)(lc)
    assert len(result.get("trail", [])) == n, result


@then(parsers.parse('the lifecycle_check substrate tool matches "{state}"'))
def _substrate_check_match(engine, lc, state):
    from agency._substrate_tools import LifecycleCheck
    result = LifecycleCheck().bind(engine)(lc, state)
    assert result.get("match") is True, result


@then(parsers.parse('the lifecycle_check substrate tool does not match "{state}"'))
def _substrate_check_no_match(engine, lc, state):
    from agency._substrate_tools import LifecycleCheck
    result = LifecycleCheck().bind(engine)(lc, state)
    assert result.get("match") is False, result


@when("I open two lifecycles serving the intent", target_fixture="lc")
def _open_two(engine, confirmed_intent):
    engine.lifecycle.open(confirmed_intent)
    return engine.lifecycle.open(confirmed_intent)


@then(parsers.parse("lifecycle.find for the intent returns {n:d} lifecycles"))
def _find_plural(engine, confirmed_intent, n):
    found = engine.lifecycle.find(confirmed_intent)
    assert len(found) == n, found
