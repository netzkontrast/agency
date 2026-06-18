# agency-scaffold: v1
"""discover.scope cluster — structure-layer verbs (Spec 317 acceptance, 318 scope).

Spec 317 lands ``acceptance`` here: it derives testable, Gherkin-shaped acceptance
criteria from the Intent's ``deliverable`` — DERIVED, never invented. Each accepted
criterion is an ``AcceptanceCriterion`` node ``VALIDATES``-edged to the Intent; an
unmeasurable criterion (a ``Then`` with no observable check) is FLAGGED, never
silently accepted. ``role="transform"``: it proposes criteria (and mints their
nodes as structured output) but does not overwrite the Intent's field — the caller
folds them via ``intent.amend`` / ``refine`` (320).
"""
from __future__ import annotations

import re

from agency.capability import verb
from agency.toolresult import ToolResult

# Vague qualifiers carrying NO observable assertion — a criterion resting only on
# these is unmeasurable (flagged). Documented + extensible (CLAUDE.md #8), not a
# frozen snapshot; the Spec 147 Driver fills sharper criteria in Slice 2.
_VAGUE_MARKERS = (
    "works well", "work well", "works great", "good", "nice", "better",
    "intuitive", "user-friendly", "user friendly", "properly", "correctly",
    "as expected", "robust", "clean", "seamless", "elegant",
)
_MIN_PART_LEN = 3


class ScopeCluster:
    """The ``acceptance`` verb — composed into ``DiscoverCapability``."""

    @verb(role="transform")
    def acceptance(self, for_intent_id: str = "") -> ToolResult:
        """Derive testable, Gherkin-shaped acceptance criteria from the Intent (transform).

        Splits the Intent's ``deliverable`` into checkable sub-parts and derives
        one criterion per part — a ``text`` statement, a Given/When/Then ``gherkin``
        triple, and a ``measurable`` bool. Unmeasurable criteria are FLAGGED, never
        dropped. Mints each as an ``AcceptanceCriterion`` ``VALIDATES``-edged to the
        Intent; does NOT overwrite the Intent's ``acceptance`` field (the caller
        folds it).

        Inputs: for_intent_id (the Intent to derive for; defaults to ``ctx.intent_id``).
        Returns: ``{criteria:[{id,text,gherkin,measurable,flagged,source}],
                 acceptance, coverage:{deliverable_parts, covered, gaps}}``.
        chain_next: fold ``acceptance`` into the Intent via ``intent.amend`` /
                    ``discover.refine`` (320); ``discover.clarity`` then re-scores.
        """
        intent = self._recall_intent(for_intent_id) or {}
        iid = for_intent_id or self.ctx.intent_id
        parts = self._split_deliverable(str(intent.get("deliverable", "")))

        criteria: list[dict] = []
        gaps: list[str] = []
        for part in parts:
            measurable = not self._is_vague(part)
            then = (f'Then "{part}" produces an observable result'
                    if measurable
                    else f'Then "{part}" — no observable check (flagged)')
            gherkin = (f"Given the deliverable is produced\n"
                       f"When the user exercises it\n{then}")
            text = f"The deliverable satisfies: {part}"
            cid = self.ctx.record_and_serve("AcceptanceCriterion", {
                "text": text, "gherkin": gherkin, "measurable": measurable})
            self.ctx.link(cid, iid, "VALIDATES")
            criteria.append({"id": cid, "text": text, "gherkin": gherkin,
                             "measurable": measurable, "flagged": not measurable,
                             "source": part})
            if not measurable:
                gaps.append(part)

        covered = sum(1 for c in criteria if c["measurable"])
        return ToolResult.success(data={
            "criteria": criteria,
            # the proposed sharpened acceptance field — measurable criteria only.
            "acceptance": "; ".join(c["text"] for c in criteria if c["measurable"]),
            "coverage": {"deliverable_parts": len(parts),
                         "covered": covered, "gaps": gaps},
        })

    # ── derivation helpers (Spec 147 Driver seam fills sharper criteria later) ──
    def _split_deliverable(self, deliverable: str) -> list[str]:
        """Split the deliverable into checkable sub-parts on clause delimiters +
        ``and`` — each part a substring of the live deliverable (derivability)."""
        raw = re.split(r"[.;,\n]|\band\b", deliverable)
        return [p.strip() for p in raw if len(p.strip()) >= _MIN_PART_LEN]

    def _is_vague(self, part: str) -> bool:
        low = part.lower()
        return any(marker in low for marker in _VAGUE_MARKERS)
