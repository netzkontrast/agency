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
