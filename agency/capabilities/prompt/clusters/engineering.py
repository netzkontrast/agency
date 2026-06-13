"""prompt.engineering — Prompt-engineering lineage (Spec 109 Slice 1).

Spec 286 P3 — extracted verbatim from ``prompt/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single PromptCapability.

engineer (renders a PromptInstance inside a token budget) + audit
(general-case reader-test simulation).
"""
from __future__ import annotations

from agency.capability import verb
from agency.toolresult import ToolResult

from ._base import (
    _DEFAULT_AUDIT_MIN_SCORE,
    _DEFAULT_TOKEN_BUDGET,
    _approx_tokens,
    _score_brief,
)


class EngineeringMixin:
    """Prompt-engineering lineage (verbs 6-7)."""

    @verb(role="act")
    def engineer(self, builder_kind: str, context: str,
                  constraints: str = "",
                  max_tokens: int = _DEFAULT_TOKEN_BUDGET) -> ToolResult:
        """Render a PromptInstance inside a token budget (act).

        Composes context + constraints into a structured prompt body using
        the canonical layout:

            # <builder_kind> prompt
            ## Context
            <context>
            ## Constraints
            <constraints>

        Records a PromptInstance node + body. Refuses to produce a body that
        exceeds ``max_tokens`` (returns INVALID_ARGUMENT instead — the
        caller revises before re-engineering).

        Inputs: builder_kind (free-form slug), context, constraints,
                max_tokens.
        Returns: ``{result, artefact}`` prompt-instance artefact.
        chain_next: ``prompt.token_budget_gate`` to gate the lifecycle.
        """
        body = (f"# {builder_kind} prompt\n\n"
                f"## Context\n{context.strip()}\n\n"
                f"## Constraints\n{(constraints or 'none').strip()}\n")
        tokens = _approx_tokens(body)
        if tokens > max_tokens:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"engineered prompt {tokens} tokens > budget {max_tokens}; "
                f"reduce context or relax constraints")
        instance_id = self.ctx.record_and_serve("PromptInstance", {
            "builder_kind": builder_kind, "rendered_body": body,
        })
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "prompt-instance",
                         "builder_kind": builder_kind,
                         "rendered_body": body,
                         "instance_id": instance_id,
                         "approx_tokens": tokens},
        })

    @verb(role="effect")
    def audit(self, prompt_body: str,
               min_score: int = _DEFAULT_AUDIT_MIN_SCORE) -> ToolResult:
        """General-case reader-test simulation for any prompt (effect).

        Inputs: prompt_body, min_score.
        Returns: ``{clarity_score, status, findings}``.
        chain_next: revise + re-audit; or ``prompt.audit_gate`` to gate.
        """
        score, findings = _score_brief(prompt_body)
        status = "passed" if score >= min_score else "failed"
        return ToolResult.success(data={
            "clarity_score": score, "status": status,
            "findings": findings,
        })
