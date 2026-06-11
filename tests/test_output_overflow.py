"""Spec 154 Slice 1 — output overflow capture + recall.

Spec 005 (output-overflow capture + recall) was Not Started. When a verb
returned more than the token budget (Spec 023), the engine truncated and
the tail was LOST even though it might hold the answer. The Claude API's
own answer to large intermediate results is to keep them out of context
and recall on demand (`claude-api` skill — programmatic tool calling).
The engine should do the same: overflow bodies go to the graph as an
Artefact, the response carries a typed recall handle, a follow-up call
fetches the slice the agent actually needs.

Slice 1 ships the pure capture + recall library:
- `capture_overflow(body, max_tokens, *, counter)` -> `OverflowResult`
  carrying the truncated head + the full body for the caller to write
  as an Artefact.
- `recall_overflow_slice(body, *, slice="", grep="", max_tokens, counter)`
  -> typed `RecallSlice` carrying the requested view of the captured
  body.
- Typed shapes: `OverflowResult`, `OverflowHandle`, `RecallSlice`.

Slice 2 wires capture into `agency/_envelope.py` (the prefix stays
byte-stable per Spec 146; only the body half is captured); Slice 3
adds `memory.recall_overflow(handle, slice, grep)` as a graph verb +
the `Artefact(kind="overflow-capture")` write + the per-invocation
provenance edges.
"""
from __future__ import annotations

import pytest

from agency._overflow import (
    OverflowHandle,
    OverflowResult,
    RecallSlice,
    capture_overflow,
    recall_overflow_slice,
)


# Deterministic per-test token counter (4 chars ≈ 1 token; matches the
# Spec 082 fallback proxy).
def _counter(text: str) -> int:
    return max(1, len(text) // 4) if text else 0


# ── pure capture ──────────────────────────────────────────────────────────
def test_short_body_returns_no_overflow():
    """Body within budget is returned as-is; no truncation, no Artefact."""
    body = "small body" * 5                                        # ~13 tokens
    r = capture_overflow(body, max_tokens=100, counter=_counter)
    assert isinstance(r, OverflowResult)
    assert r.truncated is False
    assert r.head == body
    assert r.total_tokens == _counter(body)
    assert r.returned_tokens == r.total_tokens
    assert r.full_body == body                                     # caller may still store


def test_long_body_truncates_at_budget():
    """Body over budget is truncated to ≤ max_tokens and flagged."""
    body = "lorem ipsum dolor " * 1000                             # ~4500 chars → ~1125 tokens
    r = capture_overflow(body, max_tokens=100, counter=_counter)
    assert r.truncated is True
    assert r.total_tokens > 100
    assert r.returned_tokens <= 100
    assert r.full_body == body                                     # original preserved


def test_truncation_is_monotone_in_head():
    """The truncated head is a PREFIX of the full body (no lossy
    re-encoding)."""
    body = "alpha beta gamma " * 500
    r = capture_overflow(body, max_tokens=50, counter=_counter)
    assert body.startswith(r.head)


def test_full_body_round_trip_byte_for_byte():
    """Invariant (b): the captured `full_body` reconstructs the source
    exactly (no lossy capture)."""
    body = "x" * 12345
    r = capture_overflow(body, max_tokens=50, counter=_counter)
    assert r.full_body == body


# ── recall — full slice ───────────────────────────────────────────────────
def test_recall_full_body_returns_complete_slice():
    body = "line " + "a " * 1000
    r = recall_overflow_slice(body, slice="full",
                              max_tokens=10_000, counter=_counter)
    assert isinstance(r, RecallSlice)
    assert r.body == body
    assert r.total_tokens == _counter(body)
    assert r.slice_tokens == r.total_tokens
    assert r.more_available is False


# ── recall — line-range slice ─────────────────────────────────────────────
def test_recall_by_line_range_returns_only_that_range():
    body = "\n".join(f"line {i}" for i in range(100))
    r = recall_overflow_slice(body, slice="10:15",
                              max_tokens=10_000, counter=_counter)
    # 5 lines (10..14 inclusive of start, exclusive of stop).
    assert r.body.count("\n") + 1 == 5
    assert "line 10" in r.body
    assert "line 14" in r.body
    assert "line 15" not in r.body
    assert r.total_tokens == _counter(body)
    assert r.slice_tokens == _counter(r.body)


def test_recall_line_range_clamps_to_body_length():
    body = "\n".join(f"line {i}" for i in range(5))
    r = recall_overflow_slice(body, slice="2:999",
                              max_tokens=10_000, counter=_counter)
    # Returns lines 2..end without crashing.
    assert "line 2" in r.body
    assert "line 4" in r.body
    assert r.body.count("\n") + 1 == 3


# ── recall — grep slice ───────────────────────────────────────────────────
def test_recall_by_grep_returns_only_matching_lines():
    body = "\n".join([
        "info: starting",
        "info: working",
        "error: something failed",
        "info: continuing",
        "error: another problem",
        "info: done",
    ])
    r = recall_overflow_slice(body, grep="error:",
                              max_tokens=10_000, counter=_counter)
    assert r.matches_returned == 2
    assert "something failed" in r.body
    assert "another problem" in r.body
    assert "starting" not in r.body                                # info: line dropped


def test_recall_grep_no_matches_returns_empty_body():
    body = "info: a\ninfo: b\ninfo: c"
    r = recall_overflow_slice(body, grep="never",
                              max_tokens=10_000, counter=_counter)
    assert r.body == ""
    assert r.matches_returned == 0
    assert r.more_available is False


def test_recall_grep_respects_max_tokens_budget():
    """Invariant (c): recall itself honours max_tokens (no infinite-
    recursion overflow). When matches exceed budget, `more_available`
    flags it."""
    body = "\n".join([f"error: {i}" for i in range(1000)])
    r = recall_overflow_slice(body, grep="error:",
                              max_tokens=20, counter=_counter)
    assert r.slice_tokens <= 20
    assert r.more_available is True
    assert r.matches_returned < 1000                               # truncated


# ── typed shapes / validation ─────────────────────────────────────────────
def test_recall_slice_is_frozen_dataclass():
    r = recall_overflow_slice("body", slice="full",
                              max_tokens=10, counter=_counter)
    with pytest.raises(Exception):
        r.body = "mutated"                                         # frozen


def test_overflow_handle_carries_typed_shape():
    handle = OverflowHandle(recall_handle="art_abc", total_tokens=12000,
                            returned_tokens=4000, truncated=True)
    assert handle.recall_handle == "art_abc"
    assert handle.truncated is True
    with pytest.raises(Exception):
        handle.truncated = False                                   # frozen


def test_capture_with_empty_body_is_safe():
    r = capture_overflow("", max_tokens=100, counter=_counter)
    assert r.truncated is False
    assert r.head == ""
    assert r.total_tokens == 0


def test_invalid_slice_string_returns_full_body():
    """Defensive: a malformed `slice` string falls back to the full body
    rather than crashing — the caller asked for a view and we give
    the safest one. Tested explicitly so future strictness lands here."""
    body = "one\ntwo\nthree"
    r = recall_overflow_slice(body, slice="bogus",
                              max_tokens=10_000, counter=_counter)
    assert r.body == body


# ── Codex round-1 review on PR #129 ───────────────────────────────────────
def test_counter_with_count_method_is_accepted():
    """Codex review: Spec 082's `TokenCounter` exposes `.count(text)`
    rather than `__call__`. The capture/recall API must accept it via
    the `_as_counter_fn` adapter."""

    class StubCounter:
        def count(self, text: str, model: str | None = None) -> int:
            return max(1, len(text) // 4) if text else 0

    counter = StubCounter()
    body = "x" * 1000
    r = capture_overflow(body, max_tokens=50, counter=counter)
    assert r.truncated is True
    assert r.returned_tokens <= 50
    rs = recall_overflow_slice(body, slice="full", max_tokens=50,
                                counter=counter)
    assert rs.slice_tokens <= 50


def test_capture_with_zero_budget_returns_empty_head():
    """Codex review: `max_tokens=0` must NOT spin forever on a one-
    character string. Capture mode yields an empty head + truncated."""
    body = "hello world" * 100
    r = capture_overflow(body, max_tokens=0, counter=_counter)
    assert r.truncated is True
    assert r.head == ""
    assert r.full_body == body


def test_recall_with_zero_budget_returns_empty_body_with_terminal_cursor():
    """Codex review (round-5) on PR #129: zero budget on recall must
    produce a TERMINAL cursor — `more_available=False` AND
    `next_byte_offset` advanced past the unreachable body — so a caller
    following the documented cursor contract doesn't loop on the same
    empty page forever."""
    body = "hello world" * 100
    r = recall_overflow_slice(body, slice="full", max_tokens=0,
                              counter=_counter)
    assert r.body == ""
    assert r.more_available is False                               # terminal
    assert r.next_byte_offset >= len(body)                         # past the unreachable tail


def test_recall_zero_budget_cursor_terminates_paging_loop():
    """A naive paging loop on zero-budget recall must terminate via the
    `more_available=False` signal — not spin on the stale byte_offset."""
    body = "x" * 200
    offset = 0
    iters = 0
    while iters < 5:
        iters += 1
        r = recall_overflow_slice(body, slice="full", byte_offset=offset,
                                  max_tokens=0, counter=_counter)
        if not r.more_available:
            break
        if r.next_byte_offset == offset:                            # safety: detect stall
            pytest.fail("cursor stalled — paging loop would never terminate")
        offset = r.next_byte_offset
    assert iters < 5                                                # terminated in 1 iter


def test_capture_with_negative_budget_raises_value_error():
    """Negative budget is a programming error — reject loudly at the
    boundary rather than silently truncating to nothing."""
    with pytest.raises(ValueError):
        capture_overflow("body", max_tokens=-1, counter=_counter)


def test_counter_without_call_or_count_method_raises():
    """A counter object that exposes neither `__call__` nor `.count`
    raises TypeError immediately — not on the first internal use."""
    with pytest.raises(TypeError):
        capture_overflow("body", max_tokens=10, counter=object())


# ── Codex round-2 review on PR #129 — grep match preservation ─────────────
def test_grep_truncates_at_match_boundary_not_mid_line():
    """Codex review: when a matching line is too long to fit, drop the
    WHOLE line instead of returning its start without the grep text.
    `matches_returned` reflects FULLY-included matches only."""
    # Three matching lines, each ~125 chars (~31 tokens via 4:1 proxy).
    # With budget 5 tokens (≈ 20 chars), NO whole match fits.
    long_match = "x" * 60 + " error: detail " + "y" * 50            # grep term mid-line
    body = "\n".join([long_match, long_match, long_match])
    r = recall_overflow_slice(body, grep="error:",
                              max_tokens=5, counter=_counter)
    assert r.matches_returned == 0
    assert r.body == ""
    assert r.more_available is True


def test_grep_returned_body_always_contains_grep_term_when_match_count_nonzero():
    """The body MUST contain the grep term for every match counted.
    Previously a prefix-truncate could drop the grep text while still
    reporting `matches_returned >= 1`."""
    body = "\n".join([f"error: case {i}" for i in range(50)])
    r = recall_overflow_slice(body, grep="error:",
                              max_tokens=30, counter=_counter)
    assert r.matches_returned > 0
    # Body has exactly `matches_returned` occurrences of the grep term.
    assert r.body.count("error:") == r.matches_returned


def test_grep_more_available_flag_reflects_dropped_matches():
    body = "\n".join([f"error: case {i}" for i in range(100)])
    r = recall_overflow_slice(body, grep="error:",
                              max_tokens=20, counter=_counter)
    assert r.matches_returned < 100
    assert r.more_available is True


def test_grep_fits_all_matches_reports_complete():
    body = "info: a\nerror: x\ninfo: b\nerror: y"
    r = recall_overflow_slice(body, grep="error:",
                              max_tokens=10_000, counter=_counter)
    assert r.matches_returned == 2
    assert r.more_available is False
    assert r.body == "error: x\nerror: y"


# ── Codex round-3 review on PR #129 — pagination cursors ────────────────
def test_grep_pagination_via_offset_walks_all_matches():
    """Codex review: grep with many matches must be pageable. Caller
    passes `next_match_offset` back as `offset=` until
    `more_available=False`."""
    body = "\n".join([f"error: {i}" for i in range(60)])
    seen: list[str] = []
    offset = 0
    iters = 0
    while iters < 30:                                              # safety cap
        iters += 1
        r = recall_overflow_slice(body, grep="error:", offset=offset,
                                  max_tokens=30, counter=_counter)
        if not r.body and not r.more_available:
            break
        seen.extend(line for line in r.body.split("\n") if line)
        if not r.more_available:
            break
        offset = r.next_match_offset
    # All 60 matches eventually returned via paging.
    assert len(seen) == 60
    assert all("error:" in s for s in seen)


def test_grep_skips_oversized_line_then_continues():
    """Codex review: an early matching line longer than `max_tokens`
    must be SKIPPED, not break the iteration — later fitting matches
    must still be returned in the same call."""
    huge = "error: " + "x" * 500                                   # ~127 tokens
    body = "\n".join([huge, "error: small1", "error: small2"])
    r = recall_overflow_slice(body, grep="error:",
                              max_tokens=20, counter=_counter)
    # Huge skipped; small1 + small2 should fit.
    assert "small1" in r.body
    assert "small2" in r.body
    assert "x" * 100 not in r.body                                 # huge dropped
    assert r.more_available is True                                # huge was skipped


def test_byte_offset_reconstructs_oversized_line_byte_for_byte():
    """Codex review on PR #129: a single line larger than max_tokens
    must still be reconstructible byte-for-byte via the byte_offset
    cursor (Spec 154 invariant b)."""
    long_line = "x" * 800                                          # ~200 tokens
    body = long_line                                               # single line
    pieces: list[str] = []
    byte_offset = 0
    iters = 0
    while iters < 30:                                              # safety cap
        iters += 1
        r = recall_overflow_slice(body, slice="full",
                                  byte_offset=byte_offset,
                                  max_tokens=50, counter=_counter)
        pieces.append(r.body)
        if not r.more_available:
            break
        byte_offset = r.next_byte_offset
    # Concatenation reconstructs the source byte-for-byte.
    assert "".join(pieces) == body


def test_negative_offset_raises_value_error():
    with pytest.raises(ValueError):
        recall_overflow_slice("body", offset=-1, max_tokens=10, counter=_counter)
    with pytest.raises(ValueError):
        recall_overflow_slice("body", byte_offset=-1, max_tokens=10, counter=_counter)


def test_grep_offset_past_end_returns_empty():
    body = "error: 1\nerror: 2"
    r = recall_overflow_slice(body, grep="error:", offset=10,
                              max_tokens=100, counter=_counter)
    assert r.body == ""
    assert r.matches_returned == 0
    assert r.more_available is False


# ── Codex round-4 review on PR #129 — preserve fits-alone matches ─────────
def test_grep_deferred_match_reachable_on_next_page():
    """Codex review: with varying-length matches, a line that fits
    alone but doesn't fit on the current page must be REACHABLE on a
    follow-up — not skipped past by `next_match_offset`. The 5-7-3 case:
    the 7-token line must appear in a later page even though a 3-token
    line could also fit on page 1."""
    # Three matches sized ~5, ~7, ~3 tokens (4:1 proxy → 20/28/12 chars).
    body = "\n".join([
        "err1 " + "a" * 15,                                        # ~5 tokens
        "err2 " + "b" * 25,                                        # ~7 tokens
        "err3 " + "c" * 7,                                         # ~3 tokens
    ])
    seen: list[str] = []
    offset = 0
    iters = 0
    while iters < 6:
        iters += 1
        r = recall_overflow_slice(body, grep="err",
                                  offset=offset, max_tokens=9,
                                  counter=_counter)
        for line in r.body.split("\n"):
            if line:
                seen.append(line)
        if not r.more_available:
            break
        if r.next_match_offset == offset:                          # safety against infinite loop
            break
        offset = r.next_match_offset
    # All three matches reachable — none lost in the seam.
    assert sum("err1" in s for s in seen) == 1
    assert sum("err2" in s for s in seen) == 1
    assert sum("err3" in s for s in seen) == 1


def test_grep_oversized_skip_doesnt_block_paging_completion():
    """An oversized middle match is permanently skipped (unfittable
    anywhere); paging must still terminate cleanly and reach later
    fitting matches."""
    huge = "err " + "x" * 200                                      # ~51 tokens
    body = "\n".join([
        "err small1",
        huge,
        "err small2",
    ])
    seen: list[str] = []
    offset = 0
    iters = 0
    while iters < 5:
        iters += 1
        r = recall_overflow_slice(body, grep="err",
                                  offset=offset, max_tokens=20,
                                  counter=_counter)
        for line in r.body.split("\n"):
            if line:
                seen.append(line)
        if not r.more_available and r.next_match_offset >= 3:      # stop signal
            break
        if r.next_match_offset == offset:                          # safety
            break
        offset = r.next_match_offset
    assert any("small1" in s for s in seen)
    assert any("small2" in s for s in seen)
    assert not any("x" * 100 in s for s in seen)                   # huge dropped permanently
