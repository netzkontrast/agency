"""Shared prosody helpers — deterministic, driver-free text math.

Lifted from music/_main.py + novel/_main.py post Round-1 sc-analyze
finding F2 ("_syllables_word duplicates music's _syllables; same
heuristic, two implementations, drift risk").

Both music's `lyric_report` family and novel's `analyze_readability`
need a syllable count; promoting to a shared module so one fix lands
in one place. Per CLAUDE.md §"Derivability audit".
"""
from __future__ import annotations

_VOWELS = "aeiouy"


def syllables(word: str) -> int:
    """Deterministic vowel-group syllable count (≥ 1 for non-empty word).

    Same heuristic both music + novel previously hand-rolled in their
    own modules. Char-walk + final-silent-e rule.
    """
    w = word.lower().strip()
    count, prev_vowel = 0, False
    for ch in w:
        is_vowel = ch in _VOWELS
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if w.endswith("e") and count > 1:
        count -= 1
    return max(1, count) if w else 0
