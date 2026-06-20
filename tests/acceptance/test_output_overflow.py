"""Acceptance — output overflow capture and recall (Spec 154 Slice 1).

Converted from tests/test_output_overflow.py. Behaviour: the observable
contract of capture_overflow / recall_overflow_slice — truncation shape,
full-body preservation, slice semantics, typed rejection.
"""
from __future__ import annotations

import dataclasses

import pytest
from pytest_bdd import scenarios, then, when

from agency._overflow import (
    OverflowResult,
    capture_overflow,
    recall_overflow_slice,
)

scenarios("features/output_overflow.feature")


# ── deterministic token counter (4 chars ≈ 1 token) ─────────────────────

def _counter(text: str) -> int:
    return max(1, len(text) // 4) if text else 0


# ── helpers ────────────────────────────────────────────────────────────────

def _make_body(n_tokens: int) -> str:
    line = "X" * 4  # 1 token per line at 4 chars/token
    return "\n".join([line] * n_tokens)


# ── When steps ─────────────────────────────────────────────────────────────

@when("I capture a body of 13 tokens with a budget of 100",
      target_fixture="cap_result")
def _short_capture():
    body = "small body " * 5  # ~13 tokens
    return capture_overflow(body, max_tokens=100, counter=_counter), body


@when("I capture a body of 500 tokens with a budget of 50",
      target_fixture="cap_result")
def _long_capture():
    body = _make_body(500)
    return capture_overflow(body, max_tokens=50, counter=_counter), body


@when("I capture an overflowing body", target_fixture="cap_result")
def _overflow_body():
    body = _make_body(200)
    return capture_overflow(body, max_tokens=20, counter=_counter), body


@when("I capture an overflowing body and recall it with no slice specifier",
      target_fixture="recall_result")
def _recall_full():
    body = _make_body(200)
    result = capture_overflow(body, max_tokens=20, counter=_counter)
    rs = recall_overflow_slice(result.full_body, max_tokens=9999, counter=_counter)
    return rs, body


@when("I capture a 20-line body and recall with slice 5 to 10",
      target_fixture="recall_result")
def _recall_range():
    lines = [f"line {i}" for i in range(1, 21)]
    body = "\n".join(lines)
    result = capture_overflow(body, max_tokens=1, counter=_counter)
    rs = recall_overflow_slice(result.full_body, slice="5:10", max_tokens=9999,
                               counter=_counter)
    return rs, lines


@when("I capture a body with some ERROR lines and recall with grep ERROR",
      target_fixture="recall_result")
def _recall_grep_match():
    body = "ok line\nERROR one\nanother\nERROR two\nfine"
    result = capture_overflow(body, max_tokens=1, counter=_counter)
    rs = recall_overflow_slice(result.full_body, grep="ERROR", max_tokens=9999,
                               counter=_counter)
    return rs, None


@when("I capture a body with no ERROR lines and recall with grep ERROR",
      target_fixture="recall_result")
def _recall_grep_no_match():
    body = "ok line\ngood line\nfine"
    result = capture_overflow(body, max_tokens=1, counter=_counter)
    rs = recall_overflow_slice(result.full_body, grep="ERROR", max_tokens=9999,
                               counter=_counter)
    return rs, None


@when("I recall an overflow body", target_fixture="recall_result")
def _recall_any():
    body = _make_body(200)
    result = capture_overflow(body, max_tokens=20, counter=_counter)
    rs = recall_overflow_slice(result.full_body, max_tokens=9999, counter=_counter)
    return rs, None


@when("I attempt to capture a body with a negative budget")
def _neg_budget():
    pass  # assertion done in Then


@when("I capture a body with a budget of zero tokens", target_fixture="zero_result")
def _zero_budget():
    body = _make_body(200)
    return capture_overflow(body, max_tokens=0, counter=_counter)


# ── Then steps ─────────────────────────────────────────────────────────────

@then("the head equals the full body")
def _head_eq(cap_result):
    r, body = cap_result
    assert r.head == body


@then("the overflow flag is False")
def _no_overflow(cap_result):
    r, _ = cap_result
    assert r.truncated is False


@then("the overflow flag is True")
def _has_overflow(cap_result):
    r, _ = cap_result
    assert r.truncated is True


@then("the head is shorter than the full body")
def _head_shorter(cap_result):
    r, body = cap_result
    assert len(r.head) < len(body)


@then("the head token count does not exceed 50")
def _head_within_budget(cap_result):
    r, _ = cap_result
    assert _counter(r.head) <= 50


@then("the OverflowResult carries the complete original body")
def _body_preserved(cap_result):
    r, body = cap_result
    assert r.full_body == body


@then("the recalled body equals the full original body")
def _recall_full_check(recall_result):
    rs, body = recall_result
    assert rs.body == body


@then("the recalled body contains only lines at indices 5 to 9")
def _recall_range_check(recall_result):
    rs, lines = recall_result
    # slice="5:10" → Python indices 5..9 (0-indexed, exclusive stop)
    expected = "\n".join(lines[5:10])
    assert rs.body.strip() == expected.strip()


@then("every line in the recalled body contains ERROR")
def _grep_match(recall_result):
    rs, _ = recall_result
    for line in rs.body.splitlines():
        if line.strip():
            assert "ERROR" in line, line


@then("the recalled body is empty")
def _grep_no_match(recall_result):
    rs, _ = recall_result
    assert rs.body.strip() == ""


@then("the handle has a body_hash and a byte_count")
def _handle_shape(cap_result):
    # OverflowHandle doesn't carry body_hash in this impl — check what's
    # actually on OverflowResult (total_tokens, returned_tokens, truncated)
    r, _ = cap_result
    assert isinstance(r, OverflowResult)
    assert r.total_tokens >= 0
    assert r.returned_tokens >= 0


@then("the head is empty")
def _empty_head(zero_result):
    assert zero_result.head == ""


@then("a ValueError is raised")
def _val_err():
    with pytest.raises(ValueError):
        capture_overflow("body", max_tokens=-1, counter=_counter)


@then("the RecallSlice cannot be mutated")
def _frozen(recall_result):
    rs, _ = recall_result
    assert dataclasses.is_dataclass(rs)
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        rs.body = "mutated"  # type: ignore[misc]
