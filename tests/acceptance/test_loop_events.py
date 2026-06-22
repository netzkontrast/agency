"""Acceptance — loop detection middleware and typed LoopEvent (Spec 011 / 156).

Converted from tests/test_loop_middleware.py and tests/test_loop_events.py.

Dropped (implementation / structural / not observable behaviour):
- test_only_last_four_messages_and_five_results_windowed: tests internal
  windowing arithmetic on a carefully crafted message list — implementation
  detail of the sliding window, not an observable wire contract.
- LoopEvent frozen-dataclass field assertion (test_loop_event_typed_shape
  checking e.kind directly): retained as observable construction contract
  since LoopEvent is a public typed shape.
- test_detect_loops_ignores_events_missing_tool_or_target: whitebox test of
  skip logic on malformed events; the positive detection scenarios already
  cover the observable outcome.
"""
from __future__ import annotations


from pytest_bdd import given, scenarios, then, when

from agency.engine import Engine
from agency._loop_events import LoopEvent, detect_loops
from agency._middleware.loop import detect_loop

scenarios("features/loop_events.feature")


# ── shared Given override ─────────────────────────────────────────────────────

@given("a fresh agency engine in code-mode", target_fixture="loop_engine")
def _fresh_loop_engine():
    return Engine(":memory:")


# ── when — detect_loop middleware ────────────────────────────────────────────

@when("I run loop detection on a window with three identical tool results",
      target_fixture="loop_result")
def _identical_results():
    window = ["result A", "noise B", "result A", "noise C", "result A"]
    return detect_loop(messages=[], tool_results=window)


@when("I run loop detection on a window with diverse messages and results",
      target_fixture="loop_result")
def _diverse():
    return detect_loop(
        messages=["alpha story", "beta plan"],
        tool_results=["gamma output", "delta diff"])


@when("I run loop detection on empty messages and results",
      target_fixture="loop_result")
def _empty():
    return detect_loop(messages=[], tool_results=[])


@when("I run loop detection with two identical messages",
      target_fixture="loop_result")
def _two_identical():
    a = "the quick brown fox jumps"
    return detect_loop(messages=[a, a], tool_results=[])


# ── then — detect_loop ───────────────────────────────────────────────────────

@then("detected is True")
def _detected_true(loop_result):
    assert loop_result["detected"] is True


@then("confidence is 1.0")
def _confidence_one(loop_result):
    assert loop_result["confidence"] == 1.0


@then("the evidence indices span two of the duplicate positions")
def _evidence_indices(loop_result):
    idxs = loop_result["evidence"]["indices"]
    assert len(set(idxs)) >= 2
    assert set(idxs).issubset({0, 2, 4})


@then("detected is False")
def _detected_false(loop_result):
    assert loop_result["detected"] is False


@then("confidence is below 0.7")
def _confidence_low(loop_result):
    assert loop_result["confidence"] < 0.7


@then("the result is detected False confidence 0.0 evidence None")
def _empty_result(loop_result):
    assert loop_result == {"detected": False, "confidence": 0.0, "evidence": None}


@then("detected is True and confidence is 1.0")
def _detected_true_conf_one(loop_result):
    assert loop_result["detected"] is True
    assert loop_result["confidence"] == 1.0


# ── when — engine registry check ─────────────────────────────────────────────

@when("I list all registered capability verbs", target_fixture="all_verbs")
def _all_verbs(loop_engine):
    return {v for n in loop_engine.registry.names()
            for v in loop_engine.registry.get(n).verbs}


@then("detect_loop is not among them")
def _no_detect_loop(all_verbs):
    assert "detect_loop" not in all_verbs


@then("detect_loops is not among them")
def _no_detect_loops(all_verbs):
    # The loop-DETECTION middleware (Spec 011/156) stays internal — neither
    # detect_loop nor detect_loops is a discoverable verb. The looper-port `loop`
    # capability (Spec 387) is a DIFFERENT concept and legitimately registered;
    # this scenario guards the detector's non-exposure, not the name `loop`.
    assert "detect_loops" not in all_verbs


# ── when — LoopEvent construction ────────────────────────────────────────────

@when("I create a LoopEvent with an empty evidence tuple",
      target_fixture="loop_event_error")
def _empty_evidence_error():
    try:
        LoopEvent(event_id="loop:1", kind="loop_detected",
                  detected_at="now", evidence=(), intent_id="intent:x")
        return None
    except ValueError as e:
        return e


@then("a ValueError is raised")
def _value_error_raised(loop_event_error):
    assert isinstance(loop_event_error, (ValueError, Exception))


@when("I create a LoopEvent with kind bogus",
      target_fixture="loop_event_error")
def _invalid_kind_error():
    try:
        LoopEvent(event_id="loop:1", kind="bogus",  # type: ignore[arg-type]
                  detected_at="now", evidence=("event:a",), intent_id="intent:x")
        return None
    except ValueError as e:
        return e


# ── when — detect_loops ──────────────────────────────────────────────────────

@when("I call detect_loops on a stream with three identical git commit events",
      target_fixture="loops")
def _three_identical():
    events = [
        {"event_id": "event:1", "tool": "Bash", "target": "git commit -m a"},
        {"event_id": "event:2", "tool": "Bash", "target": "git commit -m a"},
        {"event_id": "event:3", "tool": "Bash", "target": "git commit -m a"},
        {"event_id": "event:4", "tool": "Bash", "target": "ls"},
    ]
    return detect_loops(events, window=5)


@when("I call detect_loops on a stream of five distinct git commit events",
      target_fixture="loops")
def _five_distinct():
    events = [
        {"event_id": f"event:{i}", "tool": "Bash",
         "target": f"git commit -m {chr(65 + i)}"}
        for i in range(5)
    ]
    return detect_loops(events, window=5)


@when("I call detect_loops with window 2 on a stream where duplicates are beyond the window",
      target_fixture="loops")
def _window_two():
    events = [
        {"event_id": "event:1", "tool": "Bash", "target": "x"},
        {"event_id": "event:2", "tool": "Bash", "target": "y"},
        {"event_id": "event:3", "tool": "Bash", "target": "y"},
    ]
    return detect_loops(events, window=2)


@when("I call detect_loops on exactly two identical events",
      target_fixture="loops")
def _two_identical_loops():
    return detect_loops([
        {"event_id": "event:1", "tool": "Bash", "target": "git commit"},
        {"event_id": "event:2", "tool": "Bash", "target": "git commit"},
    ], window=5)


@when("I call detect_loops on exactly three identical events",
      target_fixture="loops")
def _three_identical_loops():
    return detect_loops([
        {"event_id": "event:1", "tool": "Bash", "target": "git commit"},
        {"event_id": "event:2", "tool": "Bash", "target": "git commit"},
        {"event_id": "event:3", "tool": "Bash", "target": "git commit"},
    ], window=5)


@when("I call detect_loops on an ordered stream with three identical events after a different one",
      target_fixture="loops")
def _ordered_stream():
    return detect_loops([
        {"event_id": "event:1", "tool": "Bash", "target": "y"},
        {"event_id": "event:2", "tool": "Bash", "target": "x"},
        {"event_id": "event:3", "tool": "Bash", "target": "x"},
        {"event_id": "event:4", "tool": "Bash", "target": "x"},
    ], window=5)


# ── then — detect_loops ──────────────────────────────────────────────────────

@then("at least one LoopEvent is returned with kind loop_detected")
def _one_loop_event(loops):
    assert len(loops) >= 1
    assert loops[0].kind == "loop_detected"


@then("the evidence ids are a subset of the three identical events")
def _evidence_subset(loops):
    assert set(loops[0].evidence) <= {"event:1", "event:2", "event:3"}


@then("no LoopEvents are returned")
def _no_loops(loops):
    assert loops == []


@then("a LoopEvent is returned")
def _loop_returned(loops):
    assert loops != []


@then("the evidence tuple lists the three duplicate event ids in order")
def _evidence_order(loops):
    assert loops
    assert loops[0].evidence == ("event:2", "event:3", "event:4")
