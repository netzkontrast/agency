"""Intent clarity — the substrate readiness signals + score (Spec 307 §Refinement).

The clarity score is the home of the "is this intent clear enough to confirm?"
question. It lives HERE, at the substrate, so the gate can sit on
``Intent.confirm`` (unbypassable — the canonical ``capture_and_confirm`` runs it
too) rather than in a capability a caller can skip. The ``discover`` capability's
``clarity`` verb and ``_clarity_inputs`` helper REUSE these functions, so there is
a single source of truth (CLAUDE.md rule 4 — no second source).

Every signal is COMPUTED from the live graph (derivability audit), never stored —
the score rises as the discovery children record their nodes/edges.
"""
from __future__ import annotations


# Documented, tunable readiness threshold (CLAUDE.md #8) — not a frozen snapshot.
CLARITY_THRESHOLD = 0.6


def clarity_signals(memory, intent_id: str, draft_prefix: str = "") -> dict[str, bool]:
    """The five independent readiness signals for an Intent (each a live-graph read).

    ``memory`` is any object exposing ``recall(id)`` + ``neighbors(id, edge,
    direction)`` (the substrate ``Memory`` or a ``CapabilityContext``). ``draft_prefix``
    lets the interview's placeholder fields (Spec 309) count as "not yet a real
    triple"; empty for the bare substrate caller.

      - ``has_triple``            — purpose/deliverable/acceptance are real (non-empty,
        not an interview draft placeholder)
      - ``acceptance_measurable`` — an ``AcceptanceCriterion`` ``VALIDATES`` the Intent
        with ``measurable`` truthy (Spec 317)
      - ``ambiguities_resolved``  — no ``CLARIFIES``-linked ``ClarificationQuestion`` is
        still ``pending`` (Spec 311)
      - ``grounded``              — a ``Citation`` ``GROUNDS`` the Intent (Spec 312)
      - ``scope_bounded``         — a ``ScopeBoundary`` ``BOUNDS`` the Intent (Spec 318)
    """
    intent = memory.recall(intent_id) or {}

    def _field_ok(field: str) -> bool:
        value = str(intent.get(field, "")).strip()
        if not value:
            return False
        return not (draft_prefix and value.startswith(draft_prefix))

    triple_ok = all(_field_ok(f) for f in ("purpose", "deliverable", "acceptance"))
    criteria = memory.neighbors(intent_id, "VALIDATES", direction="in")
    questions = memory.neighbors(intent_id, "CLARIFIES", direction="in")
    return {
        "has_triple": triple_ok,
        "acceptance_measurable": any(c.get("measurable") for c in criteria),
        "ambiguities_resolved": not any(
            q.get("status") == "pending" for q in questions),
        "grounded": bool(memory.neighbors(intent_id, "GROUNDS", direction="in")),
        "scope_bounded": bool(memory.neighbors(intent_id, "BOUNDS", direction="in")),
    }


def clarity_score(memory, intent_id: str, draft_prefix: str = "") -> float:
    """Normalized 0.0-1.0 clarity score — equal-weighted fraction of satisfied
    signals (the simplest monotone default; resolving a signal never lowers it)."""
    signals = clarity_signals(memory, intent_id, draft_prefix)
    total = len(signals) or 1
    return sum(1 for ok in signals.values() if ok) / total
