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
from typing import Callable


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
Counter = Callable[[str], int]


def capture_overflow(body: str, *, max_tokens: int, counter: Counter) -> OverflowResult:
    """Inspect a body against `max_tokens`; either pass through or
    truncate the inline slice (`head`) while preserving the full source
    (`full_body`) for a follow-up `recall_overflow`.

    Truncation is monotone — `head` is a PREFIX of `full_body`. Empty
    bodies are safe. The token counter is injected so tests can pin a
    deterministic proxy; production wires the Spec 082 `TokenCounter`.
    """
    total = counter(body)
    if total <= max_tokens:
        return OverflowResult(
            head=body, full_body=body,
            total_tokens=total, returned_tokens=total,
            truncated=False,
        )
    # Truncate by character count using the counter's per-call rate
    # (`total / len(body)`); this preserves the monotone-prefix
    # invariant on the head. Pick a slice that the counter scores at
    # ≤ max_tokens by binary-searching downward from the proportional
    # estimate (cheap; never overshoots).
    body_len = len(body)
    # Proportional cut: assume tokens scale ~linearly with chars.
    estimate = max(1, (max_tokens * body_len) // max(1, total))
    head = body[:estimate]
    while head and counter(head) > max_tokens:
        # Trim 10% per iteration until we fit (typically 1-2 rounds).
        head = head[: max(1, int(len(head) * 0.9))]
    return OverflowResult(
        head=head, full_body=body,
        total_tokens=total, returned_tokens=counter(head),
        truncated=True,
    )


def recall_overflow_slice(
    body: str, *,
    slice: str = "full",                                           # "full" | "<start>:<stop>"
    grep: str = "",
    max_tokens: int,
    counter: Counter,
) -> RecallSlice:
    """Return a typed view of `body` honouring `max_tokens`.

    Selection priority: `grep` (if non-empty) → line filter; else
    `slice` (`"full"` or `"<start>:<stop>"`) → line-range slice. Either
    way, the returned body is then itself truncated to `max_tokens`
    so recall never spawns a recursive-overflow situation
    (invariant c).
    """
    total = counter(body)
    if grep:
        matches = [line for line in body.split("\n") if grep in line]
        return _truncate_to_budget(
            "\n".join(matches), total_tokens=total,
            matches_returned=len(matches),
            max_tokens=max_tokens, counter=counter,
        )
    if slice == "full":
        return _truncate_to_budget(
            body, total_tokens=total, matches_returned=0,
            max_tokens=max_tokens, counter=counter,
        )
    rng = _parse_slice(slice)
    if rng is None:
        # Malformed slice — return the full body (defensive default;
        # caller asked for a view, give the safest one).
        return _truncate_to_budget(
            body, total_tokens=total, matches_returned=0,
            max_tokens=max_tokens, counter=counter,
        )
    start, stop = rng
    lines = body.split("\n")
    selected = lines[start:stop]
    return _truncate_to_budget(
        "\n".join(selected), total_tokens=total, matches_returned=0,
        max_tokens=max_tokens, counter=counter,
    )


def _truncate_to_budget(
    body: str, *, total_tokens: int, matches_returned: int,
    max_tokens: int, counter: Counter,
) -> RecallSlice:
    """Helper — emit a `RecallSlice` honouring `max_tokens`. The
    `more_available` flag distinguishes "fully delivered" from
    "truncated for budget"."""
    cur = counter(body)
    if cur <= max_tokens:
        return RecallSlice(
            body=body, slice_tokens=cur, total_tokens=total_tokens,
            matches_returned=matches_returned, more_available=False,
        )
    # Truncate as in `capture_overflow`. We approximate proportionally
    # then shrink until we fit.
    body_len = len(body)
    estimate = max(1, (max_tokens * body_len) // max(1, cur))
    truncated = body[:estimate]
    while truncated and counter(truncated) > max_tokens:
        truncated = truncated[: max(1, int(len(truncated) * 0.9))]
    # When grep produced matches, count how many of them survived.
    if matches_returned:
        kept = truncated.count("\n") + (1 if truncated else 0)
        matches_returned = min(matches_returned, kept)
    return RecallSlice(
        body=truncated, slice_tokens=counter(truncated),
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
