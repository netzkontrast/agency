# agency-scaffold: v1
"""discover.clarify — the ambiguity-resolution loop (Spec 311).

Finds what is still vague in a draft Intent, asks ONE targeted question per
ambiguity (composing discover.ask — 310 owns the well-formed-question contract),
folds each verbatim answer back into the Intent BI-TEMPORALLY (intent.amend —
supersede, prior revision retained), and records a CLARIFIES trail — until the
Intent's residual ambiguity drops below threshold or a max-rounds budget is hit.

The ambiguity heuristics live in data/ambiguity-signals.json (the Driver seam,
Spec 147, sharpens questions from GROUNDS evidence in Slice 2). Answer-flow is the
`answers` map (the harness folds the verbatim answer per ambiguity kind).
"""
from __future__ import annotations

import json
from pathlib import Path

from agency.capability import verb
from agency.toolresult import ToolResult

# Named, tunable budget (CLAUDE.md #8) — the score above which a field reads
# ambiguous, not a magic number sprinkled in the loop.
_AMBIGUITY_THRESHOLD = 0.5
_SIGNALS_CACHE: list | None = None


def _ambiguity_signals() -> list:
    global _SIGNALS_CACHE
    if _SIGNALS_CACHE is None:
        path = Path(__file__).resolve().parent.parent / "data" / "ambiguity-signals.json"
        _SIGNALS_CACHE = json.loads(path.read_text(encoding="utf-8"))["signals"]
    return _SIGNALS_CACHE


class ClarifyCluster:
    """The ``clarify`` verb — composed into ``DiscoverCapability``."""

    @verb(role="act")
    def clarify(self, for_intent_id: str = "", answers: dict | None = None,
                max_rounds: int = 5) -> ToolResult:
        """Resolve a draft Intent's ambiguities, folding each answer back (act).

        Scores the Intent against the ambiguity-signals registry; for each
        unresolved ambiguity above threshold (highest first) composes
        ``discover.ask`` for a targeted question, folds the verbatim answer via
        ``intent.amend`` (bi-temporal supersede — the prior revision is kept), and
        records a ``CLARIFIES`` edge to the Intent's stable identity. Loops until
        residual ambiguity is below threshold or ``max_rounds`` is hit.

        Inputs: for_intent_id (defaults to ``ctx.intent_id``); answers (the folded
                ``{ambiguity_kind → verbatim answer}`` map); max_rounds (budget).
        Returns: ``{intent_id (latest revision), rounds:[{ambiguity_kind, score,
                 question_id, answer, amended_to}], residual_ambiguity, exited_by:
                 "below_threshold"|"max_rounds"}``.
        chain_next: ``discover.clarity`` re-scores; the confirm gate reads it.
        """
        answers = dict(answers or {})
        original = for_intent_id or self.ctx.intent_id
        current = original
        rounds: list[dict] = []

        for _ in range(max_rounds):
            unresolved = [s for s in self._score_ambiguities(current)
                          if s[1] >= _AMBIGUITY_THRESHOLD]
            if not unresolved:
                break
            unresolved.sort(key=lambda s: -s[1])
            picked = next((s for s in unresolved if answers.get(s[0])), None)
            if picked is None:
                break  # no folded answer can resolve any remaining ambiguity
            kind, score, field, template = picked
            answer = answers.pop(kind)

            intent = self._recall_intent(current) or {}
            # Compose discover.ask (rule 4) — the targeted question, tagged with
            # the detected ambiguity_kind; context derived from the offending field.
            asked = self.ask(
                context=[{"id": f"field:{field}",
                          "text": str(intent.get(field, "")) or f"the {field}"},
                         {"id": f"kind:{kind}",
                          "text": f"resolve the {kind} ambiguity in {field}"}],
                ambiguity_kind=kind, question=template)
            question_id = asked.data["question_id"] if asked.ok else ""
            if question_id:
                # CLARIFIES anchors to the Intent's STABLE identity (the user-owned
                # root); amends produce bi-temporal revisions beneath it.
                self.ctx.link(question_id, original, "CLARIFIES")
                self.fold_answer(question_id, answer)   # pending -> answered

            new_id = self.ctx.engine.intent.amend(current, **{field: answer})
            rounds.append({"ambiguity_kind": kind, "score": score,
                           "question_id": question_id, "answer": answer,
                           "amended_to": new_id})
            current = new_id

        scored = self._score_ambiguities(current)
        residual = max((s[1] for s in scored), default=0.0)
        exited_by = "below_threshold" if residual < _AMBIGUITY_THRESHOLD else "max_rounds"
        return ToolResult.success(data={
            "intent_id": current, "rounds": rounds,
            "residual_ambiguity": residual, "exited_by": exited_by})

    def _score_ambiguities(self, intent_id: str) -> list:
        """Score each registry signal on the Intent: ``1.0`` ambiguous (field is a
        draft placeholder or below its word floor) else ``0.0`` — binary + monotone
        so a folded answer that fills the field strictly lowers its kind's score.
        Returns ``[(kind, score, field, template), ...]``."""
        from .interview import DRAFT_FIELD_PREFIX
        intent = self._recall_intent(intent_id) or {}
        out = []
        for sig in _ambiguity_signals():
            val = str(intent.get(sig["field"], "")).strip()
            ambiguous = (val.startswith(DRAFT_FIELD_PREFIX)
                         or len(val.split()) < sig.get("min_words", 1))
            out.append((sig["kind"], 1.0 if ambiguous else 0.0,
                        sig["field"], sig["template"]))
        return out
