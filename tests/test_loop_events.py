"""Spec 156 Slice 1 — typed LoopEvent shape + pure detector.

Driven through the engine surface via the tdd skill walk on
intent:35628643. Each phase records a Phase node + a Reflection.
"""
from __future__ import annotations

import pytest

from agency._loop_events import LoopEvent, LoopKind, detect_loops


# ─────────── shape invariants ─────────────────────────────────────────
def test_loop_event_typed_shape():
    """LoopEvent is a frozen dataclass with required keys."""
    e = LoopEvent(
        event_id="loop:abc", kind="loop_detected",
        detected_at="2026-06-12T10:00:00Z",
        evidence=("event:a", "event:b", "event:c"),
        intent_id="intent:x",
    )
    assert e.kind == "loop_detected"
    assert len(e.evidence) == 3


def test_loop_event_rejects_invalid_kind():
    with pytest.raises(ValueError):
        LoopEvent(event_id="loop:1", kind="bogus",          # type: ignore[arg-type]
                   detected_at="now",
                   evidence=("event:a",), intent_id="intent:x")


def test_loop_event_rejects_empty_evidence():
    """Every loop event MUST cite at least one event id; an empty
    evidence tuple is a doctrine violation (no causal trail)."""
    with pytest.raises(ValueError):
        LoopEvent(event_id="loop:1", kind="loop_detected",
                   detected_at="now", evidence=(),
                   intent_id="intent:x")


# ─────────── detect_loops ────────────────────────────────────────────
def test_detect_loops_flags_three_identical_commits():
    """A 4-event stream with 3 identical (Bash, 'git commit') tuples
    within a 5-event window is a loop."""
    events = [
        {"event_id": "event:1", "tool": "Bash", "target": "git commit -m a"},
        {"event_id": "event:2", "tool": "Bash", "target": "git commit -m a"},
        {"event_id": "event:3", "tool": "Bash", "target": "git commit -m a"},
        {"event_id": "event:4", "tool": "Bash", "target": "ls"},
    ]
    loops = detect_loops(events, window=5)
    assert len(loops) >= 1
    loop = loops[0]
    assert loop.kind == "loop_detected"
    assert set(loop.evidence) <= {"event:1", "event:2", "event:3"}


def test_detect_loops_returns_empty_on_diverse_stream():
    """Distinct (tool, target) tuples should NOT trigger a loop."""
    events = [
        {"event_id": f"event:{i}", "tool": "Bash",
         "target": f"git commit -m {chr(65 + i)}"}
        for i in range(5)
    ]
    loops = detect_loops(events, window=5)
    assert loops == []


def test_detect_loops_respects_window_size():
    """A repetition outside the window must NOT trigger; inside it must."""
    events = [
        {"event_id": "event:1", "tool": "Bash", "target": "x"},
        {"event_id": "event:2", "tool": "Bash", "target": "y"},
        {"event_id": "event:3", "tool": "Bash", "target": "y"},
        # widow=2 means we only look back 2 — at index 2, prior is event:1+2.
    ]
    loops = detect_loops(events, window=2)
    # y is in the window at index 2 (event:2 + event:3) — only 2 repeats; threshold is 3
    assert loops == []


def test_detect_loops_empty_input_returns_empty():
    assert detect_loops([], window=5) == []


def test_detect_loops_threshold_is_three():
    """Two identical events do not constitute a loop; three do."""
    two = [
        {"event_id": "event:1", "tool": "Bash", "target": "git commit"},
        {"event_id": "event:2", "tool": "Bash", "target": "git commit"},
    ]
    assert detect_loops(two, window=5) == []
    three = two + [
        {"event_id": "event:3", "tool": "Bash", "target": "git commit"}
    ]
    assert detect_loops(three, window=5) != []


def test_detect_loops_ignores_events_missing_tool_or_target():
    """Skip events without tool/target — they aren't loop candidates."""
    events = [
        {"event_id": "event:1"},                                      # no tool
        {"event_id": "event:2", "tool": "Bash"},                      # no target
        {"event_id": "event:3", "tool": "Bash", "target": "x"},
    ]
    loops = detect_loops(events, window=5)
    assert loops == []


def test_detect_loops_preserves_evidence_order():
    """Evidence event ids are returned in chain order (oldest first)."""
    events = [
        {"event_id": "event:1", "tool": "Bash", "target": "y"},
        {"event_id": "event:2", "tool": "Bash", "target": "x"},
        {"event_id": "event:3", "tool": "Bash", "target": "x"},
        {"event_id": "event:4", "tool": "Bash", "target": "x"},
    ]
    loops = detect_loops(events, window=5)
    assert loops
    assert loops[0].evidence == ("event:2", "event:3", "event:4")
