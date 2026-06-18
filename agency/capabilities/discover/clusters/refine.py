# agency-scaffold: v1
"""discover.refine cluster — Intent clarity scoring + (Spec 320) refinement.

Spec 322 lands ``clarity`` here (the cluster that also holds ``refine``, Spec 320):
the Intent-readiness scorer the ``guided-discovery`` discipline's confirm gate
reads. ``clarity`` is READ-ONLY — it scores the five independent readiness signals
(``_base._clarity_inputs``), each computed from the live discovery graph, and
returns ``{score, missing, ready}`` so the agent knows the next discovery step.
The ``clarity_gate`` composite + override token is Spec 322 Slice 2.
"""
from __future__ import annotations

from agency.capability import verb
from agency.toolresult import ToolResult

# Documented, tunable readiness threshold (CLAUDE.md #8) — not a frozen snapshot.
CLARITY_THRESHOLD = 0.6


class RefineCluster:
    """The ``clarity`` verb — composed into ``DiscoverCapability``."""

    @verb(role="transform")
    def clarity(self, for_intent_id: str = "") -> ToolResult:
        """Score a captured Intent's clarity / readiness (transform, read-only).

        The score is the normalized sum of five INDEPENDENT readiness signals,
        each computed from the live discovery graph (has-triple · acceptance-
        measurable · ambiguities-resolved · grounded · scope-bounded). Equal
        weights (the simplest monotone default, CLAUDE.md #8). Writes nothing
        beyond the Invocation — it reads existing discovery nodes/edges.

        Inputs: for_intent_id (the Intent to score; defaults to ``ctx.intent_id``
                — named ``for_intent_id`` not ``intent_id`` to avoid colliding with
                the invoke serving-intent arg, per the document/dogfood convention).
        Returns: ``{score (0.0-1.0), missing:[signal,...], ready (score>=threshold),
                 signals:{name:bool}}``.
        chain_next: resolve a ``missing`` signal (clarify/acceptance/ground/scope),
                    then re-score.
        """
        signals = self._clarity_inputs(for_intent_id)
        total = len(signals) or 1
        satisfied = sum(1 for ok in signals.values() if ok)
        score = satisfied / total
        return ToolResult.success(data={
            "score": round(score, 3),
            "missing": sorted(name for name, ok in signals.items() if not ok),
            "ready": score >= CLARITY_THRESHOLD,
            "signals": signals,
        })
