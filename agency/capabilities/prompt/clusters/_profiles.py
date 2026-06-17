"""prompt.clusters._profiles — goal-aware evaluation profiles (Spec 305/306).

``evaluate`` scores a prompt body against a criteria PROFILE selected by its
TARGET. A user-prompt is judged on the 5-dimension quality grid (clarity /
specificity / context / completeness / structure — ported from
prompt-architect's ``prompt_evaluator.py``). Spec 306 registers FUNCTIONAL
profiles (``skilldoc`` / ``tool-desc`` / ``template``) whose flags name the
TARGET GOAL they violate (e.g. ``role_padding`` — a function needs no Role).

A profile is a callable ``(body) -> (scores: dict[str,float], flags: list[str])``
registered in ``PROFILES`` by target name. The verb computes the overall score +
pass/fail; profiles only score + flag. This is the seam 306 extends — register a
new target here, no verb change.
"""
from __future__ import annotations

import re
from typing import Callable

# Tunable pass threshold on the 0-10 grid (CLAUDE.md rule 8 — documented budget).
_DEFAULT_EVAL_MIN_SCORE: float = 6.0


def _clamp(score: float) -> float:
    return max(0.0, min(10.0, score))


# ─────────────────────────── user-prompt 5-dim grid ───────────────────────────
# Ported from prompt-architect/scripts/prompt_evaluator.py (MIT, ckelsoe).

_VAGUE = ("thing", "stuff", "something", "anything", "maybe", "kind of", "sort of")
_QUESTION = ("what", "how", "why", "when", "where", "who")
_PRONOUN_START = ("it", "this", "that", "they")
_SPEC_KW = ("format", "length", "style", "words", "paragraphs", "sections", "points")
_CONTEXT_KW = ("for", "because", "since", "background", "context", "situation",
               "currently", "previously", "in order to", "so that")
_CONSTRAINT_KW = ("must", "should", "cannot", "don't", "avoid", "limit", "maximum",
                  "minimum", "required", "constraint", "restriction")
_WHAT_KW = ("create", "write", "analyze", "generate", "make", "develop", "build")
_WHY_KW = ("because", "for", "to", "so that", "in order to", "goal", "purpose")
_HOW_KW = ("using", "with", "through", "by", "via", "format", "style", "approach")
_FORMAT_KW = ("format", "structure", "as a", "in the form of", "list", "table",
              "paragraph", "json", "markdown")


def _clarity(body: str) -> tuple[float, list[str]]:
    low, score, flags = body.lower(), 5.0, []
    vague = sum(1 for w in _VAGUE if w in low)
    if vague:
        score -= min(vague * 0.5, 3)
        flags.append(f"clarity: {vague} vague term(s)")
    if any(w in low for w in _QUESTION):
        score += 2
    else:
        flags.append("clarity: goal could be more explicit")
    first = body.split()[0].lower() if body.split() else ""
    if first in _PRONOUN_START:
        score -= 2
        flags.append("clarity: starts with an ambiguous pronoun")
    return _clamp(score), flags


def _specificity(body: str) -> tuple[float, list[str]]:
    score, flags, wc = 5.0, [], len(body.split())
    if wc < 5:
        score -= 3
        flags.append("specificity: very brief — likely missing details")
    elif wc < 10:
        score -= 1
        flags.append("specificity: quite brief")
    elif wc > 15:
        score += 1
    if any(c.isdigit() for c in body):
        score += 1
    if sum(1 for w in body.split() if w and w[0].isupper() and w not in ("I", "A")):
        score += 1
    specs = sum(1 for k in _SPEC_KW if k in body.lower())
    if specs:
        score += min(specs, 2)
    else:
        flags.append("specificity: no format/length specifications")
    return _clamp(score), flags


def _context(body: str) -> tuple[float, list[str]]:
    low, score, flags = body.lower(), 5.0, []
    ctx = sum(1 for k in _CONTEXT_KW if k in low)
    if ctx == 0:
        score -= 3
        flags.append("context: no contextual information provided")
    elif ctx >= 2:
        score += 2
    else:
        score += 1
    if any(w in low for w in _CONSTRAINT_KW):
        score += 1
    else:
        flags.append("context: no constraints or limitations specified")
    return _clamp(score), flags


def _completeness(body: str) -> tuple[float, list[str]]:
    low, score, flags = body.lower(), 5.0, []
    if any(w in low for w in _WHAT_KW):
        score += 2
    else:
        score -= 2
        flags.append("completeness: what to do is unclear")
    if any(w in low for w in _WHY_KW):
        score += 1
    else:
        flags.append("completeness: missing purpose or goal")
    if any(w in low for w in _HOW_KW):
        score += 1
    else:
        flags.append("completeness: missing guidance on approach")
    if any(w in low for w in _FORMAT_KW):
        score += 1
    else:
        flags.append("completeness: output format not specified")
    return _clamp(score), flags


def _structure(body: str) -> tuple[float, list[str]]:
    score, flags = 5.0, []
    sentences = [s.strip() for s in body.split(".") if s.strip()]
    if len(sentences) > 1:
        score += 1
    else:
        flags.append("structure: single sentence — could use more structure")
    has_bullets = any(c in body for c in ("-", "•", "*")) or "\n" in body
    if has_bullets:
        score += 1
    has_sections = any(m in body for m in (":", "\n\n", "1.", "2.", "First", "Second"))
    if has_sections:
        score += 1
    if any(len(s.split()) > 40 for s in sentences):
        score -= 1
        flags.append("structure: very long sentence(s) — could split")
    wc = len(body.split())
    if wc > 30 and not has_sections and not has_bullets:
        score -= 1
        flags.append("structure: longer prompt would benefit from structure")
    elif wc > 30 and (has_sections or has_bullets):
        score += 1
    return _clamp(score), flags


def user_prompt_profile(body: str) -> tuple[dict, list[str]]:
    """The 5-dimension quality grid for a user-facing prompt."""
    dims = {
        "clarity": _clarity, "specificity": _specificity, "context": _context,
        "completeness": _completeness, "structure": _structure,
    }
    scores, flags = {}, []
    for name, fn in dims.items():
        s, f = fn(body)
        scores[name] = round(s, 1)
        flags.extend(f)
    return scores, flags


# Target → profile callable. Spec 306 registers functional profiles here.
# AGENCY-DRIFT: evaluate-profiles — keep in sync with the `target` values the
# `evaluate` verb advertises + the 306 functional-framework family.
PROFILES: dict[str, Callable[[str], tuple[dict, list[str]]]] = {
    "user-prompt": user_prompt_profile,
}


def overall(scores: dict) -> float:
    return round(sum(scores.values()) / len(scores), 2) if scores else 0.0
