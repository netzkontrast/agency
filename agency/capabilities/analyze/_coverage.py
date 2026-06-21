"""Spec 383 §1 — source-coverage matrix loader (the brooks dozen).

The twelve classic software-engineering books are vendored as cited data in
``data/source-coverage.json`` (from brooks-lint ``_shared/source-coverage.md``).
This module is the single reader of that matrix — the companion to ``_decay``:
``decay-risks.json`` says WHICH risk a symptom evidences, ``source-coverage.json``
says WHICH principle of WHICH book grounds the Iron-Law Source, and lists the
``do_not_ignore`` guardrails that keep a citation from becoming shallow
book-name-dropping.

One book registry, two consumers: every book a decay risk cites
(``decay-risks.json`` ``sources[].book``) MUST exist here (the grounding
invariant — Spec 383). No book definition is duplicated in prose-in-code
(CLAUDE.md rule 2) and the book COUNT is whatever the data defines, never a
pinned literal (rule 8) — adding a book needs no code edit.
"""
from __future__ import annotations

import json
from pathlib import Path

SOURCE_COVERAGE_PATH = Path(__file__).parent / "data" / "source-coverage.json"


# AGENCY-DRIFT: source-coverage — the book registry's second consumer (decay-risks
# is the first). Every book a decay risk cites (decay-risks.json sources[].book)
# MUST appear here; the "decay-risk coverage" gate in scripts/check-drift (Spec 383
# §4) fails on a cited-but-absent book (no shallow name-dropping).
def load_source_coverage() -> dict[str, dict]:
    """The per-book source-coverage matrix: ``{book: entry}``.

    Excludes metadata keys (those starting with ``_``, e.g. the ``_source``
    provenance marker). Each entry carries ``encoded`` (the principles the book
    contributes to the risk set) and ``do_not_ignore`` (the false-positive
    guardrails). The book count is derived from this file (rule 8)."""
    raw = json.loads(SOURCE_COVERAGE_PATH.read_text(encoding="utf-8"))
    return {book: entry for book, entry in raw.items() if not book.startswith("_")}
