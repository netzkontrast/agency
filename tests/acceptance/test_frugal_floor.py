"""Acceptance — frugal safety-floor gate (Spec 332 Slice 4).

`_frugal.safety_floor_intact()` is a decidable predicate: at every level but off
the FULL render carries every safety-floor marker and the COMPACT render names
the floor. It is gate-recordable via the existing `gate.check` verb.
"""
from __future__ import annotations

from pytest_bdd import given, parsers, scenarios, then, when

from agency import _frugal
from conftest import invoke

scenarios("features/frugal_floor.feature")


@given("an open lifecycle", target_fixture="lifecycle_id")
def _open_lifecycle(engine, confirmed_intent):
    lc = engine.memory.record("Lifecycle", {"state": "working", "phase": 0})
    engine.memory.link(lc, confirmed_intent, "SERVES")
    return lc


@when("I evaluate the frugal safety-floor predicate", target_fixture="pred")
def _eval():
    return _frugal.safety_floor_intact()


@when("I evaluate the predicate against a render that drops a floor marker",
      target_fixture="pred")
def _eval_broken():
    dropped = _frugal.SAFETY_FLOOR_MARKERS[0]

    def bad_render(level=None, *, mode="full"):
        return _frugal.render(level, mode=mode).replace(dropped, "")

    return _frugal.safety_floor_intact(render_fn=bad_render)


@then("the safety-floor predicate passes")
def _passes(pred):
    assert pred["ok"], pred


@then("it checked every non-off level")
def _all_levels(pred):
    expected = {lvl for lvl in _frugal.LEVELS if lvl != "off"}
    assert set(pred["checked"]) == expected, pred


@then("the safety-floor predicate fails")
def _fails(pred):
    assert not pred["ok"], pred


@then("the findings name the dropped marker")
def _names(pred):
    dropped = _frugal.SAFETY_FLOOR_MARKERS[0]
    assert pred["findings"], pred
    assert any(dropped in str(f.get("missing", "")) for f in pred["findings"]), pred


@when(parsers.parse('I record the safety-floor predicate as a gate "{name}"'),
      target_fixture="gate_res")
def _record(engine, confirmed_intent, lifecycle_id, name):
    pred = _frugal.safety_floor_intact()
    res, _ = invoke(engine, confirmed_intent, "gate", "check",
                    lifecycle_id=lifecycle_id, name=name, passed=pred["ok"],
                    evidence=f"checked {pred['checked']}")
    return res


@then("the recorded gate passed")
def _gate_passed(gate_res):
    inner = gate_res.get("result", gate_res)
    assert inner.get("passed") is True, gate_res
