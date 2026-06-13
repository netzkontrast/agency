"""prompt.dossier — Research-dossier lineage (Spec 109 Slice 1).

Spec 286 P3 — extracted verbatim from ``prompt/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single PromptCapability.

intent_capture → catalog_list → brief_render → brief_audit → brief_finalize.
Produces dossier-shaped research deliverables.
"""
from __future__ import annotations

from agency.capability import verb
from agency.toolresult import ToolResult

from ._base import _DEFAULT_AUDIT_MIN_SCORE, _score_brief
from ..ontology import CATALOG_CATEGORY, DELIVERABLE_KIND


# Minimal seed catalog for Slice 1 — the full YAML-loaded catalog lands in
# Slice 2. These 6 modules cover the load-bearing dossier-author phases:
# discovery / sources / synthesis (A); structure / framing (B); audit /
# anti-pattern checks (C).
_SEED_CATALOG: list[dict] = [
    {"category": "A", "identifier": "M01",
     "name": "discovery", "summary": "primary-source identification"},
    {"category": "A", "identifier": "M02",
     "name": "source-curation", "summary": "weight + lineage tagging"},
    {"category": "A", "identifier": "M03",
     "name": "synthesis", "summary": "cross-source distillation"},
    {"category": "B", "identifier": "M04",
     "name": "structure", "summary": "deliverable shape selection"},
    {"category": "B", "identifier": "M05",
     "name": "framing", "summary": "audience + voice alignment"},
    {"category": "C", "identifier": "M06",
     "name": "audit", "summary": "clarity + completeness review"},
]


class DossierMixin:
    """Research-dossier lineage (verbs 1-5)."""

    @verb(role="act")
    def intent_capture(self, seed_query: str, topic: str,
                        deliverable: str = "dossier",
                        success_criteria: str = "") -> ToolResult:
        """Record a structured ResearchIntent SERVING the intent (act).

        Inputs: seed_query, topic, deliverable (one of DELIVERABLE_KIND),
                success_criteria (multi-line).
        Returns: ``{intent_id, deliverable}``.
        chain_next: ``prompt.catalog_list`` then ``prompt.brief_render``.
        """
        if deliverable not in DELIVERABLE_KIND:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"deliverable={deliverable!r} not in {sorted(DELIVERABLE_KIND)}")
        rid = self.ctx.record("ResearchIntent", {
            "seed_query": seed_query, "topic": topic,
            "deliverable": deliverable,
            "success_criteria": success_criteria,
        })
        self.ctx.link(rid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "intent_id": rid, "deliverable": deliverable,
        })

    @verb(role="transform")
    def catalog_list(self, category: str = "") -> ToolResult:
        """List bundled CatalogModule entries optionally filtered by category (transform).

        Slice 1 ships a 6-module seed (M01-M06 across categories A/B/C);
        Slice 2 loads the full catalog from ``data/reference/research-module-catalog.yaml``.

        Inputs: category (one of CATALOG_CATEGORY or ``""`` for all).
        Returns: ``{modules: [{category, identifier, name, summary}], count}``.
        chain_next: ``prompt.brief_render`` with the selected module identifiers.
        """
        if category and category not in CATALOG_CATEGORY:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"category={category!r} not in {sorted(CATALOG_CATEGORY)}")
        modules = [m for m in _SEED_CATALOG
                   if not category or m["category"] == category]
        return ToolResult.success(data={
            "modules": modules, "count": len(modules),
        })

    @verb(role="act")
    def brief_render(self, research_intent_id: str,
                      module_ids: str = "") -> ToolResult:
        """Render a ResearchBrief body from the dossier-skeleton template (act).

        Records a ResearchBrief node + body; edges to the source
        ResearchIntent via RENDERS_FROM.

        Inputs: research_intent_id (the ResearchIntent node id from
                ``prompt.intent_capture``; the reserved ``intent_id`` is the
                serving Intent so this verb's input is namespaced), module_ids
                (comma-separated CatalogModule identifiers, e.g. ``"M01,M03,M06"``).
        Returns: ``{result, artefact}`` research-dossier artefact.
        chain_next: ``prompt.brief_audit`` to gate.
        """
        intent_node = self.ctx.recall(research_intent_id)
        if intent_node is None:
            return ToolResult.failure(
                "NOT_FOUND",
                f"research_intent_id={research_intent_id!r} not found")
        skeleton = self.ctx.template("dossier-skeleton")
        body = skeleton.template if skeleton is not None else ""
        # Substitute intent fields
        body = body.replace("[topic]", intent_node.get("topic", ""))
        body = body.replace("[deliverable]",
                            intent_node.get("deliverable", "dossier"))
        body = body.replace(
            "[criteria]", intent_node.get("success_criteria", ""))
        if module_ids:
            body = body.replace(
                "- [Catalog modules drawn from `prompt.catalog_list`]",
                "\n".join(f"- {m.strip()}" for m in module_ids.split(",")))
        brief_id = self.ctx.record("ResearchBrief", {
            "intent": research_intent_id, "body": body,
        })
        self.ctx.link(brief_id, research_intent_id, "RENDERS_FROM")
        self.ctx.link(brief_id, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "research-dossier",
                         "intent_ref": research_intent_id,
                         "brief_id": brief_id,
                         "body": body},
        })

    @verb(role="effect")
    def brief_audit(self, brief_id: str,
                     min_score: int = _DEFAULT_AUDIT_MIN_SCORE) -> ToolResult:
        """Rule-based clarity audit of a ResearchBrief (effect).

        Scores 0-100 on heuristics: vague words → penalty; missing bracket
        markers → penalty; over default token budget → penalty. Below
        ``min_score`` records a BriefAudit with ``status='failed'``;
        else ``passed``.

        Inputs: brief_id, min_score (default 70).
        Returns: ``{audit_id, clarity_score, status, missing_sections}``.
        chain_next: revise + re-audit OR ``prompt.brief_finalize``.
        """
        brief_node = self.ctx.recall(brief_id)
        if brief_node is None:
            return ToolResult.failure(
                "NOT_FOUND", f"brief_id={brief_id!r} not found")
        body = brief_node.get("body", "")
        score, findings = _score_brief(body)
        status = "passed" if score >= min_score else "failed"
        audit_id = self.ctx.record("BriefAudit", {
            "brief": brief_id, "clarity_score": score, "status": status,
        })
        self.ctx.link(audit_id, brief_id, "AUDITS")
        self.ctx.link(audit_id, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "audit_id": audit_id, "clarity_score": score,
            "status": status,
            "missing_sections": findings.get("missing", []),
        })

    @verb(role="effect")
    def brief_finalize(self, brief_id: str) -> ToolResult:
        """Finalize a ResearchBrief — flips its status (effect).

        Inputs: brief_id.
        Returns: ``{brief_id, finalized}``.
        chain_next: deliver the dossier downstream.
        """
        brief_node = self.ctx.recall(brief_id)
        if brief_node is None:
            return ToolResult.failure(
                "NOT_FOUND", f"brief_id={brief_id!r} not found")
        self.ctx.update(brief_id, {"finalized": True})
        return ToolResult.success(data={
            "brief_id": brief_id, "finalized": True,
        })
