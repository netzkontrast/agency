"""Spec 350 Slice 1 — relevance filter (content-aware output trimmer).

Pure ``relevance_filter(text, profile) -> dict`` that extracts signal lines from
verbose output by include/exclude regex patterns + neighbour context.  Never
truncates silently (CLAUDE.md #9): ``elided`` + ``locator`` always present in
the return so callers know how much was dropped and where to find the full text.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any


def relevance_filter(text: str, profile: dict[str, Any]) -> dict:
    """Content-aware include/exclude filter over lines of ``text``.

    Profile keys (all optional):
    - ``include``  — list of regex patterns; a line is kept if ANY matches.
                     Empty / absent = keep all (then apply exclude).
    - ``exclude``  — list of regex patterns; exclude wins over include.
    - ``context``  — int, neighbour lines to keep around each match (default 0).
    - ``budget``   — int, max chars of ``kept`` on the wire; 0 = unlimited.
                     Caps the *return*, never the stored capture (Spec 350 §3).
    - ``unit``     — ``"line"`` (default; section support is Slice 2).

    Returns::

        {
          "kept":    str,   # matched lines + context, joined by newline
          "matched": int,   # number of *matched* lines (before context expansion)
          "elided":  int,   # lines NOT in the kept set
          "locator": str,   # sha16 cursor — always present (CLAUDE.md #9)
        }

    Fail-open contract: a bad regex is silently skipped; a missing/empty profile
    returns all lines unchanged (``elided=0``).
    """
    lines = (text or "").splitlines()
    total = len(lines)
    sha16 = hashlib.sha256((text or "").encode()).hexdigest()[:16]
    locator = f"sha16:{sha16}"

    include_pats = profile.get("include") or []
    exclude_pats = profile.get("exclude") or []
    context_n = max(0, int(profile.get("context") or 0))
    budget = int(profile.get("budget") or 0)

    include_res = _compile_all(include_pats)
    exclude_res = _compile_all(exclude_pats)

    # Step 1 — matched indices (include, or all-keep when include is empty)
    if include_res:
        matched_idx = {i for i, ln in enumerate(lines)
                       if any(r.search(ln) for r in include_res)}
    else:
        matched_idx = set(range(total))

    # Step 2 — exclude wins
    if exclude_res:
        matched_idx = {i for i in matched_idx
                       if not any(r.search(lines[i]) for r in exclude_res)}

    matched_count = len(matched_idx)

    # Step 3 — expand to context window
    if context_n and matched_idx:
        keep_idx: set[int] = set()
        for i in matched_idx:
            keep_idx.update(range(max(0, i - context_n), min(total, i + context_n + 1)))
    else:
        keep_idx = set(matched_idx)

    # Step 4 — build kept text in line order
    kept_lines = [lines[i] for i in sorted(keep_idx)]
    kept = "\n".join(kept_lines)
    elided_count = total - len(keep_idx)

    # Step 5 — budget bounds the WIRE return, not the store (CLAUDE.md #9)
    if budget and len(kept) > budget:
        kept = kept[:budget] + (
            f"\n… {elided_count} lines elided — full text at {locator}"
        )

    return {
        "kept": kept,
        "matched": matched_count,
        "elided": elided_count,
        "locator": locator,
    }


def _compile_all(patterns: list[str]) -> list[re.Pattern]:
    """Compile each pattern; silently skip bad ones (fail-open for hook path)."""
    out: list[re.Pattern] = []
    for p in patterns:
        try:
            out.append(re.compile(p))
        except re.error:
            pass
    return out
