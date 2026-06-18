"""prompt.gates — composite gate verbs (Spec 109 Slice 1).

Spec 286 P3 — extracted verbatim from ``prompt/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single PromptCapability.

The 2 composite gate verbs called by walkable skills: token_budget_gate +
audit_gate. Both delegate to the ``gate`` capability's ``check`` verb.
"""
from __future__ import annotations

from agency.capability import verb
from agency.toolresult import ToolResult, Codes

from ._base import (
    _DEFAULT_AUDIT_MIN_SCORE,
    _DEFAULT_TOKEN_BUDGET,
    _approx_tokens,
    _score_brief,
)


class GatesMixin:
    """2 composite gate verbs — called by walkable skills."""

    @verb(role="effect")
    def token_budget_gate(self, lifecycle_id: str,
                           prompt_body: str,
                           max_tokens: int = _DEFAULT_TOKEN_BUDGET) -> ToolResult:
        """Computed token-budget gate — passes iff approx_tokens ≤ max_tokens (effect).

        Inputs: lifecycle_id, prompt_body, max_tokens.
        Returns: ``{gate, passed, tokens, max_tokens}`` or typed GATE_FAILED.
        chain_next: on failure, revise + re-engineer + re-gate.
        """
        tokens = _approx_tokens(prompt_body)
        passed = tokens <= max_tokens
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="token-budget", passed=passed,
                      evidence=f"approx_tokens={tokens}, max={max_tokens}")
        if not passed:
            return ToolResult.failure(
                Codes.GATE_FAILED,
                f"token-budget: {tokens} > {max_tokens}")
        return ToolResult.success(data={
            "gate": "token-budget", "passed": True,
            "tokens": tokens, "max_tokens": max_tokens,
        })

    @verb(role="effect")
    def audit_gate(self, lifecycle_id: str, prompt_body: str,
                    min_score: int = _DEFAULT_AUDIT_MIN_SCORE) -> ToolResult:
        """Computed audit gate — passes iff clarity_score ≥ min_score (effect).

        Inputs: lifecycle_id, prompt_body, min_score.
        Returns: ``{gate, passed, score, status}`` or typed GATE_FAILED.
        chain_next: on failure, revise + re-audit.
        """
        score, _ = _score_brief(prompt_body)
        passed = score >= min_score
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="audit", passed=passed,
                      evidence=f"clarity_score={score}, min={min_score}")
        if not passed:
            return ToolResult.failure(
                Codes.GATE_FAILED,
                f"audit: clarity_score={score} < {min_score}")
        return ToolResult.success(data={
            "gate": "audit", "passed": True,
            "score": score, "status": "passed",
        })
