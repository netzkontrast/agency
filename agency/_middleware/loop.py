"""Loop-detection middleware (Spec 011, port of the-agency-system Plan 119).

A pure, stdlib-only signal: do the recent messages / tool results repeat enough
to indicate the agent is stuck in a loop? Jaccard similarity over 3-char
shingles, pairwise max over the last 4 messages + last 5 tool results (≤ 9² = 81
pairs), detected when the max ≥ 0.7.

This is **middleware, not a concept** (CORE.md:17): `detect_loop` is never
registered as a capability verb and never sources its own history — the caller
(a future hooks layer) supplies `messages`/`tool_results`. v1 ships the helper
only; the Plan-119 `UserPromptSubmit` hook, the 2-note/3-turn throttle, and the
`session_log_query` message source are DEFERRED as middleware (Agency has no
hook layer or session-message store yet).
"""
from __future__ import annotations

from typing import Optional

_WINDOW_MESSAGES = 4
_WINDOW_TOOL_RESULTS = 5
_THRESHOLD = 0.7
_SHINGLE = 3


def _shingles(s: str) -> set[str]:
    """3-char shingles after lower/whitespace-normalisation. Strings shorter
    than the shingle width degrade to a single whole-string token."""
    norm = " ".join(s.lower().split())
    if len(norm) < _SHINGLE:
        return {norm} if norm else set()
    return {norm[i:i + _SHINGLE] for i in range(len(norm) - _SHINGLE + 1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def detect_loop(messages: list[str], tool_results: list[str]) -> dict:
    """Detect a repetition loop in the recent message/tool-result window.

    Inputs: messages (recent agent/user messages), tool_results (recent tool
            outputs). The caller supplies history; this helper never sources it.
    Returns: ``{detected: bool, confidence: float, evidence}`` where
             ``confidence`` is the max pairwise Jaccard over the windowed items
             and ``evidence`` (when detected) is
             ``{indices: [i, j], items: [str, str], jaccard: float}`` citing the
             two driving items by their position in the combined window
             (messages first, then tool results). Empty input →
             ``{detected: False, confidence: 0.0, evidence: None}``.
    chain_next: a future hooks layer decides whether to emit a self-interrupt
                note; this function records nothing (it is pure).
    """
    window = list(messages[-_WINDOW_MESSAGES:]) + list(tool_results[-_WINDOW_TOOL_RESULTS:])
    if len(window) < 2:
        return {"detected": False, "confidence": 0.0, "evidence": None}

    shingled = [_shingles(item) for item in window]
    best = 0.0
    best_pair: Optional[tuple[int, int]] = None
    for i in range(len(window)):
        for j in range(i + 1, len(window)):
            score = _jaccard(shingled[i], shingled[j])
            if score > best:
                best = score
                best_pair = (i, j)

    if best_pair is None or best < _THRESHOLD:
        return {"detected": False, "confidence": round(best, 4), "evidence": None}

    i, j = best_pair
    return {
        "detected": True,
        "confidence": round(best, 4),
        "evidence": {"indices": [i, j], "items": [window[i], window[j]],
                     "jaccard": round(best, 4)},
    }
