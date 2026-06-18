"""discover.clusters._base — the shared mixin every child cluster composes.

Spec 308 establishes the foundation; child specs (309-325) add their helpers
here as they implement (``_record_turn`` for interview/clarify, ``_session`` /
``_session_of`` for the session lifecycle, ``_clarity_inputs`` for the Spec 322
score). The scaffold ships only the one helper that is genuinely shared from day
one — ``_recall_intent`` (the Spec 091 ambient-intent pattern) — so we don't
land speculative, untraversed surface (CLAUDE.md dormant-surface audit).
"""
from __future__ import annotations


class DiscoverCluster:
    """Shared base for the ``discover`` cluster mixins.

    Carries cross-cluster helpers; composed (mixins first, ``CapabilityBase``
    last) into the single ``DiscoverCapability``. ``self.ctx`` is the
    ``CapabilityContext`` injected by the engine on every verb call.
    """

    def _recall_intent(self, intent_id: str = "") -> dict | None:
        """The serving intent's node (Spec 091 ambient pattern).

        Defaults to ``self.ctx.intent_id`` so a child verb can read the intent
        it serves without threading the id through every signature.
        """
        return self.ctx.recall(intent_id or self.ctx.intent_id)

    def fold_answer(self, question_id: str, answer: str) -> dict:
        """Resolve a pending ``ClarificationQuestion`` (Spec 308/310 shared fold).

        The second phase of the AskUser protocol: ``ask`` emits a pending
        question; the harness renders it and obtains a selection; the caller
        folds the answer here. Transitions ``pending`` → ``answered`` and stores
        the chosen answer. The caller-appropriate edge (``CLARIFIES`` for clarify
        311, ``ELICITS`` for interview 309, ``BOUNDS`` for scope 318) is the
        CALLER's job — this helper stays generic so ``ask`` remains read-only.
        Raises on an unknown ``question_id`` (the fold-back key is load-bearing).
        """
        node = self.ctx.recall(question_id)
        if node is None:
            raise ValueError(f"fold_answer: unknown question_id {question_id!r}")
        self.ctx.update(question_id, {"status": "answered", "answer": answer})
        return {"question_id": question_id, "status": "answered", "answer": answer}

    def _session(self, seed: str) -> str:
        """Open a ``DiscoverySession`` — the spine its turns hang off (Spec 307/309).

        Records the node (``seed`` · ``status="open"`` · ``clarity_score=0``) and
        SERVES the invoking intent. Shared so ``interview`` (309) / ``discover``
        (323) open a session the same way.
        """
        return self.ctx.record_and_serve(
            "DiscoverySession", {"seed": seed, "status": "open", "clarity_score": 0})

    def _record_turn(self, session_id: str, beat: int, kind: str,
                     question: str, answer: str) -> str:
        """Record one ``ElicitationTurn`` + the ``ELICITS`` edge (Spec 307/309).

        The edge runs ``DiscoverySession → ElicitationTurn`` (declare an edge ⇒
        traverse it — the interview loop reads prior turns via
        ``ctx.neighbors(session_id, "ELICITS", direction="out")``). Shared by
        ``interview`` (309) and ``clarify`` (311).
        """
        turn_id = self.ctx.record_and_serve("ElicitationTurn", {
            "beat": beat, "kind": kind, "question": question, "answer": answer})
        self.ctx.link(session_id, turn_id, "ELICITS")
        return turn_id

    def _clarity_inputs(self, intent_id: str = "") -> dict:
        """The five readiness signals Spec 322's clarity score reads — each
        COMPUTED from the live discovery graph (derivability audit), never stored.

        Returns a typed ``{signal: bool}`` bag:
          - ``has_triple``           — purpose/deliverable/acceptance are real
            (non-empty, not an interview draft placeholder)
          - ``acceptance_measurable``— an ``AcceptanceCriterion`` ``VALIDATES`` the
            Intent with ``measurable`` truthy (Spec 317)
          - ``ambiguities_resolved`` — no ``CLARIFIES``-linked ``ClarificationQuestion``
            is still ``pending`` (Spec 311)
          - ``grounded``             — a ``Citation`` ``GROUNDS`` the Intent (Spec 312)
          - ``scope_bounded``        — a ``ScopeBoundary`` ``BOUNDS`` the Intent (Spec 318)

        Signals whose source nodes/edges don't exist yet read False (missing), so
        the score rises as the discovery children land — no second source of truth.
        """
        from .interview import DRAFT_FIELD_PREFIX
        iid = intent_id or self.ctx.intent_id
        intent = self.ctx.recall(iid) or {}
        triple_ok = all(
            str(intent.get(f, "")).strip()
            and not str(intent.get(f, "")).startswith(DRAFT_FIELD_PREFIX)
            for f in ("purpose", "deliverable", "acceptance"))
        criteria = self.ctx.neighbors(iid, "VALIDATES", direction="in")
        questions = self.ctx.neighbors(iid, "CLARIFIES", direction="in")
        return {
            "has_triple": triple_ok,
            "acceptance_measurable": any(c.get("measurable") for c in criteria),
            "ambiguities_resolved": not any(
                q.get("status") == "pending" for q in questions),
            "grounded": bool(self.ctx.neighbors(iid, "GROUNDS", direction="in")),
            "scope_bounded": bool(self.ctx.neighbors(iid, "BOUNDS", direction="in")),
        }
