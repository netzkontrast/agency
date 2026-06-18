# agency-scaffold: v1
"""discover.ask — the reusable well-formed AskUser question primitive (Spec 310).

The ONE place the well-formed-question rules live (option count · recommended-
first · multiSelect gate · header budget · derive-not-invent). interview (309),
clarify (311) and scope (318) all compose this, so the rules cannot drift across
call sites. ``role="transform"``: it BUILDS + returns a payload and records ONE
``ClarificationQuestion`` node — it never mutates the Intent (the caller folds
the answer back via ``_base.fold_answer``).
"""
from __future__ import annotations

from agency.capability import verb
from agency.toolresult import Codes, ToolResult

# Named, tunable budgets (CLAUDE.md #8) — documented config, not frozen snapshots.
MIN_OPTIONS = 2
MAX_OPTIONS = 4
MAX_HEADER_LEN = 12
_RECOMMENDED_SUFFIX = " (Recommended)"


class AskCluster:
    """The ``ask`` verb — composed into ``DiscoverCapability``."""

    @verb(role="transform")
    def ask(self, context: list, question: str = "", n_options: int = 3,
            multi: bool = False, ambiguity_kind: str = "underspecified",
            header: str = "") -> ToolResult:
        """Build ONE well-formed AskUserQuestion payload from DERIVED options (transform).

        Every option is DERIVED from a supplied context item and carries that
        item's id as ``provenance``; an invented option (no resolvable
        provenance) is rejected, never shown to the user. Records a *pending*
        ``ClarificationQuestion``; the caller folds the answer back (no Intent
        mutation here — Spec 307 rule 3).

        Inputs:
          - context (list of ``{id, text}`` items — the derivation sources; >= 2)
          - question (the question text; derived from context when omitted)
          - n_options (clamped to [2, 4]); multi (multiSelect — independent axes
            only); ambiguity_kind (Spec 307 enum); header (<= 12 chars; derived
            when omitted)
        Returns: ``{payload: {question, header, options[], multiSelect},
                 question_id}``.
        chain_next: render ``payload`` via AskUserQuestion, then fold the answer
                    (``discover.clarify`` / ``interview`` / ``scope`` write the
                    caller-appropriate edge).
        """
        items = [c for c in (context or [])
                 if isinstance(c, dict) and c.get("id") and c.get("text")]
        if len(items) < MIN_OPTIONS:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"ask needs >= {MIN_OPTIONS} identified context items "
                f"(each {{id, text}}); got {len(items)}")
        n = max(MIN_OPTIONS, min(MAX_OPTIONS, n_options))

        candidates = self._derive_options(items)
        # The derivability oracle (Spec 310): every option's provenance MUST
        # resolve to a supplied item id. Drop any that don't — a manufactured
        # option (empty/absent provenance) provably cannot survive. This is a
        # REFERENTIAL check against the passed item set, immune to word overlap.
        valid_ids = {it["id"] for it in items}
        resolved = [o for o in candidates
                    if o.get("provenance") and o["provenance"] in valid_ids]
        if len(resolved) < MIN_OPTIONS:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                "no derived option resolves to a supplied context item — refusing "
                "to ask the user to choose between manufactured options")

        options = self._recommended_first(resolved[:n])
        payload = {
            "question": question.strip() or self._derive_question(items),
            "header": (header.strip()
                       or self._derive_header(ambiguity_kind))[:MAX_HEADER_LEN],
            "options": options,
            "multiSelect": bool(multi),
        }
        question_id = self.ctx.record_and_serve("ClarificationQuestion", {
            "text": payload["question"],
            "options": ", ".join(o["label"] for o in options),
            "ambiguity_kind": ambiguity_kind,
            "status": "pending",
        })
        return ToolResult.success(data={"payload": payload,
                                        "question_id": question_id})

    # ── derivation seam (Spec 147 Driver behind the typed AskPayload shape) ──
    def _derive_options(self, items: list) -> list:
        """Project context items → ``{label, description, provenance}`` options.

        Spec 310 Driver seam: a later slice routes this through the Spec 147
        structured-output Driver. Slice 1 is the DETERMINISTIC fallback — one
        option per distinct context item — so the primitive is fully exercised
        with zero LLM. Each option's ``provenance`` is the item it derives FROM,
        so the oracle's resolution check is constructive.
        """
        out = []
        for it in items:
            head = " ".join(str(it["text"]).split())[:60]
            out.append({
                "label": (head[:38] or str(it["id"])),
                "description": f"derived from {it['id']}: {head}",
                "provenance": it["id"],
            })
        return out

    def _recommended_first(self, options: list) -> list:
        """Order recommended-first (strongest signal), suffixing its label.

        'Strongest' is DERIVED (the longest evidence span — most signal), never a
        fixed index. Exactly one option carries the ``(Recommended)`` suffix.
        """
        if not options:
            return options
        strongest = max(range(len(options)),
                        key=lambda i: len(options[i]["description"]))
        ordered = ([options[strongest]]
                   + [o for i, o in enumerate(options) if i != strongest])
        first = dict(ordered[0])
        if not first["label"].endswith(_RECOMMENDED_SUFFIX):
            first["label"] = first["label"] + _RECOMMENDED_SUFFIX
        ordered[0] = first
        return ordered

    def _derive_question(self, items: list) -> str:
        return ("Which of these best matches your intent? "
                f"({len(items)} options derived from the evidence)")

    def _derive_header(self, ambiguity_kind: str) -> str:
        # A short derived column label; the caller's MAX_HEADER_LEN cap applies.
        return (ambiguity_kind or "choice").split("-")[0].capitalize()
