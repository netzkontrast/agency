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

from ._base import _approx_tokens

# Tunable pass threshold on the 0-10 grid (CLAUDE.md rule 8 — documented budget).
_DEFAULT_EVAL_MIN_SCORE: float = 6.0
# A functional doc (docstring / SkillDoc / tool-desc) earns its keep by being
# SHORT — a routing aid, not an essay. Tunable budget (rule 8): 600 tokens gives
# a clustered capability docstring room for its lineage overview + the
# Use-when/Triggers/Red-flags grammar without padding.
_FUNCTIONAL_DOC_BUDGET: int = 600


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


# ─────────────────────────── functional profiles (Spec 306) ───────────────────
# agency's own surface — docstrings / SkillDocs / tool-descs / templates — are
# FUNCTIONAL prompts: their job is correct ROUTING + INVOCATION, not persuasion.
# Their flags name the TARGET GOAL they violate (not a generic quality dip).

# The load-bearing novel heuristic (owner directive 2026-06-17: "a function
# needs no Role — it needs actionable insight"). Fires when a functional doc
# carries rhetorical role-assignment framing — the complement of `persona`
# (Spec 297), which ADDS a Role to an AGENT.
_ROLE_PADDING = re.compile(
    r"\byou are an?\b"                       # "you are a/an <role>"
    r"|\bact as\b"                           # "act as ..."
    r"|\byour role is\b"
    r"|\byou (?:should |must )?(?:act|behave|respond) as\b"
    r"|\bas an? (?:expert|specialist|senior|professional|world-class|"
    r"seasoned|experienced)\b",              # "as a senior <role>"
    re.IGNORECASE,
)
# A vague imperative is the opposite of "actionable insight" — hedge words where
# a verb-first instruction belongs.
_VAGUE_IMPERATIVE = re.compile(
    r"\b(?:helps?|tries? to|aims? to|is meant to|kind of|sort of|various|"
    r"stuff|things?)\b", re.IGNORECASE)


def _role_clean(body: str, flags: list[str]) -> float:
    if _ROLE_PADDING.search(body):
        flags.append("role_padding")
        return 2.0
    return 10.0


def _budget_score(body: str, flags: list[str]) -> float:
    if _approx_tokens(body) > _FUNCTIONAL_DOC_BUDGET:
        flags.append("over_budget")
        return 5.0
    return 10.0


def skilldoc_profile(body: str) -> tuple[dict, list[str]]:
    """Score a skill/capability docstring against the Spec 080 grammar."""
    low, flags, scores = body.lower(), [], {}
    scores["role_cleanliness"] = _role_clean(body, flags)
    if "use when" not in low and "triggers" not in low:
        flags.append("missing_trigger")
        scores["trigger_coverage"] = 3.0
    else:
        scores["trigger_coverage"] = 9.0
    if "red flag" not in low:
        flags.append("no_red_flags")
        scores["red_flag_coverage"] = 4.0
    else:
        scores["red_flag_coverage"] = 9.0
    if _VAGUE_IMPERATIVE.search(body):
        flags.append("vague_imperative")
        scores["actionability"] = 4.0
    else:
        scores["actionability"] = 8.0
    scores["budget"] = _budget_score(body, flags)
    return scores, flags


def _first_sentence(body: str) -> str:
    """The docstring's first sentence — the T1 brief (``parse_slices`` uses the
    same boundary). Up to the first ``. `` or newline."""
    text = body.strip()
    cut = len(text)
    for sep in (". ", "\n"):
        i = text.find(sep)
        if i != -1:
            cut = min(cut, i)
    return text[:cut].strip()


def tool_desc_profile(body: str) -> tuple[dict, list[str]]:
    """Score a verb docstring against the agency **Spec 023** grammar — a
    first-sentence brief (≤ 120 chars, single clause) + ``Inputs:`` +
    ``Returns:`` (the wire shape) + ``chain_next:`` — NOT a generic
    tool-description grammar. Routing is the CAPABILITY's job (``search`` /
    ``recommend`` / the SkillDoc 'When to use'); a verb carries no per-verb
    routing sentence (GOALS #1 token economy, #5 code-mode contract). Canon:
    ``docs/vision/CAPABILITY-AUTHORING.md`` §'verb docstring contract'."""
    low, flags, scores = body.lower(), [], {}
    scores["role_cleanliness"] = _role_clean(body, flags)
    # T1 brief — the load-bearing first-sentence rule. The measured harm is
    # search-token cost ∝ length (Spec 023: ≤120 chars); a ';' is the canon's
    # explicit two-clause signal. An em-dash is NOT flagged — in a within-budget
    # brief it is usually appositive (single clause), so flagging it over-counts.
    brief = _first_sentence(body)
    if len(brief) > 120 or ";" in brief:
        flags.append("long_brief")
        scores["brief"] = 4.0
    else:
        scores["brief"] = 9.0
    if "inputs:" not in low:
        flags.append("missing_inputs")
        scores["inputs"] = 4.0
    else:
        scores["inputs"] = 9.0
    if "returns:" not in low:
        flags.append("missing_returns")
        scores["returns"] = 4.0
    else:
        scores["returns"] = 9.0
    # chain_next is T3 + only needed when the verb chains; advisory, not a hard
    # fail (a terminal verb legitimately omits it).
    if "chain_next:" not in low and "chain next" not in low:
        flags.append("no_chain_next")
        scores["chaining"] = 6.0
    else:
        scores["chaining"] = 9.0
    return scores, flags


def template_profile(body: str) -> tuple[dict, list[str]]:
    """Score a render template (slots · invariants · budget)."""
    low, flags, scores = body.lower(), [], {}
    scores["role_cleanliness"] = _role_clean(body, flags)
    if "[" not in body or "]" not in body:
        flags.append("no_slots")
        scores["slots"] = 4.0
    else:
        scores["slots"] = 9.0
    if "invariant" not in low and "must" not in low:
        flags.append("no_invariants")
        scores["invariants"] = 5.0
    else:
        scores["invariants"] = 9.0
    scores["budget"] = _budget_score(body, flags)
    return scores, flags


# Target → profile callable. Spec 306 registers functional profiles here.
# AGENCY-DRIFT: evaluate-profiles — keep in sync with the `target` values the
# `evaluate` verb advertises + the 306 functional-framework family (the
# functional slugs in data/frameworks.json must equal the functional targets).
PROFILES: dict[str, Callable[[str], tuple[dict, list[str]]]] = {
    "user-prompt": user_prompt_profile,
    "skilldoc": skilldoc_profile,
    "tool-desc": tool_desc_profile,
    "template": template_profile,
}


def overall(scores: dict) -> float:
    return round(sum(scores.values()) / len(scores), 2) if scores else 0.0
