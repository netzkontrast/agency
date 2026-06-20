# agency-scaffold: v1
"""discover.refine cluster — Intent clarity scoring + (Spec 320) refinement.

Spec 322 lands ``clarity`` here (the cluster that also holds ``refine``, Spec 320):
the Intent-readiness scorer the ``guided-discovery`` discipline's confirm gate
reads. ``clarity`` is READ-ONLY — it scores the five independent readiness signals
(``_base._clarity_inputs``), each computed from the live discovery graph, and
returns ``{score, missing, ready}`` so the agent knows the next discovery step.
``clarity_gate`` (Spec 322 Slice 2) is the composite gate that wraps the score:
it delegates to ``gate.check`` for provenance recording and returns GATE_FAILED
unless the score is ready or an explicit override_token is supplied.
"""
from __future__ import annotations

from agency.capability import verb
from agency.toolresult import Codes, ToolResult

# Single source of truth for the threshold — the substrate clarity module the
# Intent.confirm gate also reads (Spec 307 §Refinement; CLAUDE.md rule 4).
from agency._clarity import CLARITY_THRESHOLD  # noqa: F401  (re-exported for callers)


class RefineCluster:
    """The ``clarity`` and ``clarity_gate`` verbs — composed into ``DiscoverCapability``."""

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

    @verb(role="effect")
    def clarity_gate(self, lifecycle_id: str, override_token: str = "",
                     min_clarity: float = CLARITY_THRESHOLD) -> ToolResult:
        """Composite clarity gate — records outcome via gate.check (effect).

        Passes iff the serving Intent's clarity score >= min_clarity OR an
        explicit override_token is provided (the deliberate escape hatch, also
        recorded so the provenance moat shows the bypass). Returns GATE_FAILED
        when the score is too low and no override_token was given.

        Inputs: lifecycle_id (Lifecycle to gate on),
                override_token (optional bypass — deliberately confirm a below-
                threshold Intent; recorded in gate evidence),
                min_clarity (threshold, default CLARITY_THRESHOLD — overridable
                per CLAUDE.md rule 8 so tests can flip the gate).
        Returns: ``{gate, passed, score, missing, override_used}`` or GATE_FAILED.
        chain_next: on failure, resolve ``missing`` signals (clarify/acceptance/
                    ground/scope), re-score with ``clarity``, then re-gate.
        """
        signals = self._clarity_inputs()
        total = len(signals) or 1
        satisfied = sum(1 for ok in signals.values() if ok)
        score = round(satisfied / total, 3)
        missing = sorted(name for name, ok in signals.items() if not ok)
        ready = score >= min_clarity
        override_used = bool(override_token)
        passed = ready or override_used
        evidence = f"clarity_score={score}, threshold={min_clarity}"
        if override_used:
            evidence += ", override_token_provided=True"
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="clarity", passed=passed, evidence=evidence)
        if not passed:
            return ToolResult.failure(
                Codes.GATE_FAILED,
                f"clarity: score={score} < {min_clarity}, missing={missing}")
        return ToolResult.success(data={
            "gate": "clarity",
            "passed": True,
            "score": score,
            "missing": missing,
            "override_used": override_used,
        })
