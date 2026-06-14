"""prompt.clusters._base — shared PromptCapability infrastructure (Spec 286 P3).

The token-approximation primitive + clarity-scoring heuristic + the
doctrine-tunable budgets, extracted verbatim from ``prompt/_main.py`` into a
base module every cluster mixin imports. ``PromptBase`` is the empty shared
base every cluster mixin and the composed ``PromptCapability`` inherit (prompt
has no driver-wiring, so the base only anchors the MRO); the scoring + token
helpers are module-level functions the mixins import. Behaviour-frozen
relocation.
"""
from __future__ import annotations


# Doctrine-tunable budgets (CLAUDE.md rule 8).
_DEFAULT_TOKEN_BUDGET: int = 4000          # default prompt-budget ceiling
_DEFAULT_AUDIT_MIN_SCORE: int = 70         # below → audit_gate blocks
_CLARITY_PENALTY_VAGUE: int = 15           # docstring-vague-words penalty
_CLARITY_PENALTY_NO_CONSTRAINTS: int = 20  # no [bracketed] markers penalty
_CLARITY_PENALTY_OVER_BUDGET: int = 40     # over-budget penalty

# Token approximation — 4 chars/token is the cl100k-band heuristic when
# tiktoken isn't installed. Spec 082's TokenCounter boundary would replace
# this on caps that opt into the `[tokens]` extra.
_CHARS_PER_TOKEN: int = 4


def _approx_tokens(text: str) -> int:
    return (len(text) + _CHARS_PER_TOKEN - 1) // _CHARS_PER_TOKEN


# ─────────────────────────── private scoring helpers ───────────────────────────
_VAGUE_WORDS = (
    "something", "thing", "stuff", "kind of", "sort of",
    "really", "very", "just", "maybe", "probably",
)


def _score_brief(body: str) -> tuple[int, dict]:
    """Score the body 0-100 + return findings dict.

    Heuristics (Spec 109 Slice 1):
      - vague words → -15 per kind
      - no [bracketed] markers (suggests no constraints declared) → -20
      - over default budget → -40

    Returns (score, {"missing": [...], "warnings": [...]})
    """
    body_lower = body.lower()
    score = 100
    findings = {"missing": [], "warnings": []}
    vague_hits = [w for w in _VAGUE_WORDS if w in body_lower]
    if vague_hits:
        score -= _CLARITY_PENALTY_VAGUE
        findings["warnings"].append({"kind": "vague_words",
                                      "hits": vague_hits[:5]})
    has_constraints = "[" in body and "]" in body
    if not has_constraints:
        score -= _CLARITY_PENALTY_NO_CONSTRAINTS
        findings["missing"].append("constraint-markers")
    if _approx_tokens(body) > _DEFAULT_TOKEN_BUDGET:
        score -= _CLARITY_PENALTY_OVER_BUDGET
        findings["warnings"].append({"kind": "over_budget",
                                      "tokens": _approx_tokens(body)})
    return max(0, score), findings


class PromptBase:
    """Shared base for the prompt cluster mixins.

    Prompt has no production-driver wiring; this base only anchors the MRO so
    cluster mixins compose cleanly with ``CapabilityBase`` (which supplies
    ``ctx``). Kept symmetric with the novel/music ``*Base`` shape (Spec 286 P3).
    """
