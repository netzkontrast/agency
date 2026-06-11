"""Spec 154 Slice 1 — output overflow capture + recall (pure library).

When a verb returns more than the token budget (Spec 023), the engine
truncates — and the truncated tail was LOST, even though it might hold
the answer. The Claude API's own answer to large intermediate results is
to keep them out of context and recall on demand (`claude-api` skill —
programmatic tool calling). The engine should do the same: overflow
bodies go to the graph as an Artefact, the response carries a typed
recall handle, a follow-up call fetches the slice the agent actually
needs.

Slice 1 ships the pure capture + recall library. Slice 2 wires capture
into `agency/_envelope.py` (the prefix stays byte-stable per Spec 146;
only the body half is captured); Slice 3 adds
`memory.recall_overflow(handle, slice, grep)` as a graph verb + writes
the `Artefact(kind="overflow-capture")` node + provenance edges.

Per CLAUDE.md rule 8: invariants are relationships, not pinned counts.
The token counter is INJECTED so tests can pin a deterministic proxy
(`4 chars ≈ 1 token`) without depending on the Spec 082 backend.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


def _as_counter_fn(counter: Any) -> Callable[[str], int]:
    """Adapt the injected `counter` to a `Callable[[str], int]`.

    Spec 082's `TokenCounter` exposes `.count(text)` rather than
    `__call__`; callers passing `engine.token_counter` or
    `resolve_token_counter()` would otherwise hit `TypeError` on the
    first `counter(body)` invocation (Codex review on PR #129).

    Accepts:
    - any callable `f(text) -> int` (the test-friendly form)
    - any object with a `.count(text)` method (Spec 082 `TokenCounter`)
    """
    if callable(counter):
        return counter
    if hasattr(counter, "count"):
        return counter.count
    raise TypeError(
        f"counter must be callable or expose .count(text); got "
        f"{type(counter).__name__}")


@dataclass(frozen=True)
class OverflowResult:
    """The return shape of `capture_overflow`. `head` is the slice the
    caller returns inline; `full_body` is the source body the caller
    writes as an `Artefact(kind="overflow-capture")` so a follow-up
    `recall_overflow` can serve a different slice."""

    head: str
    full_body: str
    total_tokens: int
    returned_tokens: int
    truncated: bool


@dataclass(frozen=True)
class OverflowHandle:
    """The typed handle the response envelope carries when overflow
    capture fires. Slice 3 wires `recall_handle` to the Artefact id."""

    recall_handle: str                                             # ArtefactId once Slice 3 wires it
    total_tokens: int
    returned_tokens: int
    truncated: bool


@dataclass(frozen=True)
class RecallSlice:
    """The typed return shape of `recall_overflow_slice`. `body` is the
    requested view; `more_available` flags when the slice was itself
    truncated to honour `max_tokens` (invariant c — recall itself
    honours the budget, no infinite-recursion overflow)."""

    body: str
    slice_tokens: int
    total_tokens: int
    matches_returned: int
    more_available: bool


# Type alias for the injected token counter.
Counter = Callable[[str], int]                                     # legacy alias (kept for type-hinting downstream)


def capture_overflow(body: str, *, max_tokens: int, counter: Any) -> OverflowResult:
    """Inspect a body against `max_tokens`; either pass through or
    truncate the inline slice (`head`) while preserving the full source
    (`full_body`) for a follow-up `recall_overflow`.

    Truncation is monotone — `head` is a PREFIX of `full_body`. Empty
    bodies are safe. The token counter is injected so tests can pin a
    deterministic proxy; production wires the Spec 082 `TokenCounter`
    (accepted via `.count(text)` per `_as_counter_fn` adapter).

    `max_tokens` must be ≥ 0. A non-positive budget yields an empty
    head with `truncated=True` so capture-mode doesn't spin forever on
    a degenerate budget (Codex review on PR #129).
    """
    if max_tokens < 0:
        raise ValueError(f"max_tokens must be ≥ 0, got {max_tokens}")
    count = _as_counter_fn(counter)
    total = count(body)
    if total <= max_tokens:
        return OverflowResult(
            head=body, full_body=body,
            total_tokens=total, returned_tokens=total,
            truncated=False,
        )
    head = _shrink_to_budget(body, max_tokens=max_tokens, count=count)
    return OverflowResult(
        head=head, full_body=body,
        total_tokens=total, returned_tokens=count(head),
        truncated=True,
    )


def _shrink_to_budget(s: str, *, max_tokens: int, count: Callable[[str], int]) -> str:
    """Trim `s` until `count(s) <= max_tokens`. Returns `""` for a
    non-positive budget or when even the first character exceeds it
    (rather than looping on a one-character string forever — Codex
    review on PR #129)."""
    if max_tokens <= 0:
        return ""
    body_len = len(s)
    if body_len == 0:
        return s
    cur = count(s)
    if cur <= max_tokens:
        return s
    # Proportional cut: assume tokens scale ~linearly with chars.
    estimate = max(1, (max_tokens * body_len) // max(1, cur))
    head = s[:estimate]
    while head:
        if count(head) <= max_tokens:
            return head
        new_len = int(len(head) * 0.9)
        if new_len >= len(head):
            new_len = len(head) - 1                                # force progress
        if new_len <= 0:
            return ""                                              # even 1 char exceeds budget
        head = head[:new_len]
    return ""


def recall_overflow_slice(
    body: str, *,
    slice: str = "full",                                           # "full" | "<start>:<stop>"
    grep: str = "",
    max_tokens: int,
    counter: Any,
) -> RecallSlice:
    """Return a typed view of `body` honouring `max_tokens`.

    Selection priority: `grep` (if non-empty) → line filter; else
    `slice` (`"full"` or `"<start>:<stop>"`) → line-range slice. Either
    way, the returned body is then itself truncated to `max_tokens`
    so recall never spawns a recursive-overflow situation
    (invariant c). `counter` may be a callable or a Spec 082
    `TokenCounter` (`.count(text)`); see `_as_counter_fn`.
    """
    if max_tokens < 0:
        raise ValueError(f"max_tokens must be ≥ 0, got {max_tokens}")
    count = _as_counter_fn(counter)
    total = count(body)
    if grep:
        # Codex review on PR #129: truncate at the MATCH boundary so the
        # returned body always contains the grep text the caller asked
        # for. Whole matching lines drop when they don't fit; never
        # partial lines (which previously left the start of a long line
        # while reporting `matches_returned=1` even though the grep
        # term was past the budget cut).
        matches = [line for line in body.split("\n") if grep in line]
        return _grep_truncate(
            matches, total_tokens=total,
            max_tokens=max_tokens, count=count,
        )
    if slice == "full":
        return _truncate_to_budget(
            body, total_tokens=total, matches_returned=0,
            max_tokens=max_tokens, count=count,
        )
    rng = _parse_slice(slice)
    if rng is None:
        # Malformed slice — return the full body (defensive default;
        # caller asked for a view, give the safest one).
        return _truncate_to_budget(
            body, total_tokens=total, matches_returned=0,
            max_tokens=max_tokens, count=count,
        )
    start, stop = rng
    lines = body.split("\n")
    selected = lines[start:stop]
    return _truncate_to_budget(
        "\n".join(selected), total_tokens=total, matches_returned=0,
        max_tokens=max_tokens, count=count,
    )


def _grep_truncate(
    matches: list[str], *, total_tokens: int,
    max_tokens: int, count: Callable[[str], int],
) -> RecallSlice:
    """Pack as many WHOLE matching lines as fit in `max_tokens` (joined
    by `\\n`). The returned body always contains the grep text in full
    for every match counted; truncation drops trailing matches rather
    than splitting one mid-line. `more_available` flags when ANY match
    was dropped so the caller knows to narrow the slice."""
    total_matches = len(matches)
    if not matches:
        return RecallSlice(
            body="", slice_tokens=0, total_tokens=total_tokens,
            matches_returned=0, more_available=False,
        )
    accepted: list[str] = []
    for line in matches:
        candidate = "\n".join(accepted + [line])
        if count(candidate) > max_tokens:
            break
        accepted.append(line)
    body = "\n".join(accepted)
    return RecallSlice(
        body=body, slice_tokens=count(body),
        total_tokens=total_tokens,
        matches_returned=len(accepted),
        more_available=len(accepted) < total_matches,
    )


def _truncate_to_budget(
    body: str, *, total_tokens: int, matches_returned: int,
    max_tokens: int, count: Callable[[str], int],
) -> RecallSlice:
    """Helper — emit a `RecallSlice` honouring `max_tokens`. The
    `more_available` flag distinguishes "fully delivered" from
    "truncated for budget"."""
    cur = count(body)
    if cur <= max_tokens:
        return RecallSlice(
            body=body, slice_tokens=cur, total_tokens=total_tokens,
            matches_returned=matches_returned, more_available=False,
        )
    # Use the shared shrink helper so the non-positive / one-char
    # safety branches apply uniformly with capture_overflow.
    truncated = _shrink_to_budget(body, max_tokens=max_tokens, count=count)
    if matches_returned:
        kept = truncated.count("\n") + (1 if truncated else 0)
        matches_returned = min(matches_returned, kept)
    return RecallSlice(
        body=truncated, slice_tokens=count(truncated),
        total_tokens=total_tokens, matches_returned=matches_returned,
        more_available=True,
    )


def _parse_slice(s: str) -> tuple[int, int] | None:
    """`"10:15"` → `(10, 15)`. Negative or non-int values yield None."""
    if not s or ":" not in s:
        return None
    head, _, tail = s.partition(":")
    try:
        start = int(head)
        stop = int(tail)
    except ValueError:
        return None
    if start < 0 or stop < 0 or stop < start:
        return None
    return start, stop
