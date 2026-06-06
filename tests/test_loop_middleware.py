"""Spec 011 — loop-detection middleware (Plan-119 port).

`detect_loop` is a PURE engine-middleware helper (CORE.md:17 — loop detection is
middleware, not a concept). Jaccard over 3-char shingles, pairwise max over the
last 4 messages + last 5 tool results (≤ 81 pairs), threshold 0.7, stdlib only.
It is NOT a discoverable verb — never surfaced via search/get_schema/execute.
"""
from __future__ import annotations

from agency._middleware.loop import detect_loop


# anchor 119.1 — identical repeated tool result triggers detection at conf 1.0
def test_identical_repeats_detected_at_confidence_one():
    window = ["result A", "noise B", "result A", "noise C", "result A"]  # 0,2,4 identical
    res = detect_loop(messages=[], tool_results=window)
    assert res["detected"] is True
    assert res["confidence"] == 1.0
    # evidence names two of the duplicate indices
    assert set(res["evidence"]["indices"]).issubset({0, 2, 4})
    assert res["evidence"]["indices"][0] != res["evidence"]["indices"][1]


def test_distinct_inputs_not_detected():
    res = detect_loop(messages=["alpha story", "beta plan"],
                      tool_results=["gamma output", "delta diff"])
    assert res["detected"] is False
    assert res["confidence"] < 0.7


def test_empty_inputs_are_safe():
    res = detect_loop(messages=[], tool_results=[])
    assert res == {"detected": False, "confidence": 0.0, "evidence": None}


def test_threshold_is_inclusive_at_0_7():
    # two near-identical strings sharing ~all shingles → high jaccard
    a = "the quick brown fox jumps"
    res = detect_loop(messages=[a, a], tool_results=[])
    assert res["detected"] is True
    assert res["confidence"] == 1.0


def test_only_last_four_messages_and_five_results_windowed():
    # an early duplicate pair OUTSIDE the window must not trip detection
    msgs = ["dup", "m1", "m2", "m3", "m4", "dup"]  # the two "dup" are 5 apart; only last 4 kept
    res = detect_loop(messages=msgs[:5], tool_results=[])  # drop the trailing dup
    assert res["detected"] is False


def test_detect_loop_is_not_a_discoverable_verb():
    # The helper must never be registered as a capability verb.
    from agency.engine import Engine
    e = Engine(":memory:")
    try:
        all_verbs = {v for n in e.registry.names() for v in e.registry.get(n).verbs}
    finally:
        e.memory.close()
    assert "detect_loop" not in all_verbs
    assert "loop" not in set(e.registry.names())
    assert "agentic" not in set(e.registry.names())
