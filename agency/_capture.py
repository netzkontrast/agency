"""Capture-full helper — the no-truncate policy (user directive 2026-06-19).

Captured DATA — tool calls (pre/post), command output, stored provenance text —
is NEVER silently truncated: a dropped tail makes the record LIE about what
actually happened, which is worse than a larger record. When a value is unusually
large we **warn** (naming the size) and keep the FULL value rather than cutting it.

This is the generalisation of CLAUDE.md rule 9 (the project index never drops
content to fit a budget) to all captured data. NOT in scope: content-hash
prefixes (`sha[:16]`), top-N list selection (`ranked[:10]`), and pure display
width (a CLI help column) — those are not data truncation and keep their slicing.
"""
from __future__ import annotations

import logging

_log = logging.getLogger("agency.capture")

# Warn (never cut) when a single captured value exceeds this many characters. A
# documented soft VISIBILITY threshold — it changes nothing about what is stored,
# it only surfaces an unusually large capture so it isn't a silent surprise.
WARN_OVER_CHARS = 100_000


def keep_full(value: str, *, label: str = "value",
              warn_over: int = WARN_OVER_CHARS) -> str:
    """Return ``value`` in FULL — never truncated (no-truncate policy).

    Warns, naming the size, when ``value`` exceeds ``warn_over`` so an unusually
    large capture is visible without being silently cut. Returns the value
    unchanged otherwise. ``None``/empty pass straight through.
    """
    if value and len(value) > warn_over:
        _log.warning("%s is %d chars — kept in full, not truncated "
                     "(no-truncate policy)", label, len(value))
    return value


def paginate(items, *, cursor: int = 0, page_size: int, kind: str = "items") -> dict:
    """Return one page of ``items`` PLUS the instruction to read the rest — the
    no-truncate complement of ``keep_full`` for a bounded RETURN (Spec 336 S1).

    The tail is **never cut**: it is reachable via ``next_cursor``, not dropped.
    ``items`` is any sequence (paginate a large text by splitting it to lines
    first, then ``"\\n".join`` each page). The agent gets a literal
    read-continuation instruction so the full set is recoverable deterministically.

    Returns ``{page, cursor, next_cursor, total, remaining, read_more}`` —
    ``read_more`` is ``""`` when the set is exhausted, else an instruction naming
    the ``cursor`` to pass on the next call.
    """
    if page_size < 1:
        raise ValueError(f"page_size must be >= 1, got {page_size}")
    seq = list(items)
    total = len(seq)
    cursor = max(0, int(cursor))
    page = seq[cursor:cursor + page_size]
    next_cursor = cursor + len(page)
    remaining = total - next_cursor
    read_more = (f"{remaining} more {kind} — call again with cursor={next_cursor} "
                 f"to read the rest." if remaining > 0 else "")
    return {"page": page, "cursor": cursor, "next_cursor": next_cursor,
            "total": total, "remaining": remaining, "read_more": read_more}
