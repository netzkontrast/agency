# agency-scaffold: v1
"""research — lead + specialists + verifier (Spec 044).

Three verbs:
  lead       (act)       — scope the question, plan specialists,
                           mint a Research node; returns the plan.
  specialist (act)       — run one bounded sub-search per role
                           (codebase | prior-reflections | doc-corpus
                           | web); records Citation nodes.
  verify     (transform) — adversarial citation check; records a
                           Verification node + per-check results.

NO LLM. NO prose generation. The capability composes deterministic
features over the graph; the document.render(scope='research-report')
follow-up projects the records into prose (Spec 043 v2 scope addition).
"""
from __future__ import annotations

import time

from agency.capability import CapabilityBase, verb
from agency.ontology import OntologyExtension

from . import _lead, _specialist, _verify


_RESEARCH_STATUSES = {"planning", "fanning-out", "verifying", "ready",
                       "blocked", "published"}
_SOURCE_KINDS = {"codebase", "reflection", "doc-corpus", "web"}
_VERIFICATION_STATUSES = {"pass", "warn", "fail"}


_DEEP_RESEARCH_SKILL = {
    "name": "deep-research",
    "kind": "discipline",
    "phases": [
        # Spec 044 §"Skill walker" — 6 phases in v2 (scope, plan,
        # fan-out, verify, render, publish). v1 ships 4: plan, fan-out,
        # verify, publish. scope is the orchestrator's responsibility
        # (refine the question); render is a v2 followup that depends
        # on document.render(scope='research-report').
        {"index": 1, "name": "plan", "produces": ["research_id", "specialists"]},
        {"index": 2, "name": "fan-out", "produces": ["citations_recorded"]},
        {"index": 3, "name": "verify", "produces": ["verification_status"]},
        {"index": 4, "name": "publish", "produces": ["published"],
          "gate": "hard"},
    ],
}


class ResearchCapability(CapabilityBase):
    name = "research"
    home = "capability"
    ontology = OntologyExtension(
        nodes={
            "Research": ["question", "depth", "started_at", "status"],
            "Citation": ["source_kind", "source_url_or_path",
                          "evidence_text", "confidence",
                          "claim_supported", "research_id"],
            "ResearchClaim": ["text", "research_id"],
            "Verification": ["research_id", "status", "started_at"],
        },
        enums={
            ("Research", "status"): _RESEARCH_STATUSES,
            ("Citation", "source_kind"): _SOURCE_KINDS,
            ("Verification", "status"): _VERIFICATION_STATUSES,
        },
        edges={"CITES", "SUPPORTS", "CONTRADICTS", "VERIFIES"},
        schemas={
            "research-report": {
                "name": "research-report",
                "required": ["research_id", "question", "claims", "citations"],
            },
        },
        skills={"deep-research": _DEEP_RESEARCH_SKILL},
    )

    @verb(role="act")
    def lead(self, question: str, depth: str = "standard") -> dict:
        """Scope a research question + plan specialists; mints a Research node.

        Inputs: question (str), depth (str — brief|standard|deep).
        Returns: ``{research_id, specialists, plan}``.
        chain_next: ``research.specialist`` per planned role.
        """
        if depth not in ("brief", "standard", "deep"):
            depth = "standard"
        specialists, plan_text = _lead.plan(question, depth)
        rid = self.ctx.record("Research", {
            "question": question,
            "depth": depth,
            "started_at": int(time.time()),
            "status": "planning",
        })
        self.ctx.link(rid, self.ctx.intent_id, "SERVES")
        return {
            "research_id": rid,
            "specialists": specialists,
            "plan": plan_text,
        }

    @verb(role="act")
    def specialist(self, research_id: str, role: str,
                   query: str,
                   search_root: str = "agency",
                   docs_root: str = "docs",
                   k: int = 5) -> dict:
        """One bounded sub-search; records Citations under the research_id.

        Inputs: research_id (str — from research.lead), role (str
        — codebase|prior-reflections|doc-corpus|web), query (str),
        search_root (str — codebase only), docs_root (str — doc-corpus
        only), k (int — max hits).
        Returns: ``{citations, summary}``.
        chain_next: more specialists OR research.verify.
        """
        if role == "codebase":
            return _specialist.run_codebase(
                self.ctx.memory, self.ctx, research_id, query,
                search_root=search_root, max_hits=k)
        if role == "prior-reflections":
            return _specialist.run_prior_reflections(
                self.ctx.memory, self.ctx, research_id, query, k=k)
        if role == "doc-corpus":
            return _specialist.run_doc_corpus(
                self.ctx.memory, self.ctx, research_id, query,
                docs_root=docs_root, max_hits=k)
        if role == "web":
            web = getattr(self.ctx.registry.engine, "web_search", None) \
                if self.ctx.registry.engine else None
            return _specialist.run_web(
                self.ctx.memory, self.ctx, research_id, query,
                web_search=web, k=k)
        return {"error": f"unknown role {role!r}; expected one of "
                          "codebase|prior-reflections|doc-corpus|web"}

    @verb(role="act")
    def verify(self, research_id: str) -> dict:
        """Adversarial citation check; emits a Verification node.

        Inputs: research_id (str — from prior research.lead).
        Returns: ``{ok, checks: {evidence-supports-claim, contradiction-cluster}}``.
        chain_next: walker's publish phase on ok=True; rerun
                    specialists on ok=False.
        """
        # Reject stale / typo'd research_ids before writing the
        # Verification — Memory.link doesn't validate endpoints, so
        # without this guard we'd record an orphan Verification linked
        # to a non-Research id (PR review r3343808276 pattern).
        res_node = self.ctx.memory.g.get_node(research_id)
        if res_node is None or "Research" not in (res_node.get("labels") or []):
            return {"ok": False, "checks": {},
                    "error": f"unknown research_id {research_id!r}"}

        embedder = getattr(self.ctx.registry.engine, "embedder", None) \
            if self.ctx.registry.engine else None
        result = _verify.run_all(self.ctx.memory, research_id, embedder=embedder)
        # Record a Verification node with rolled-up status + per-check
        # breakdown so document.render(scope='research-report') can show
        # what passed / what failed (round-4 review: the node previously
        # held only research_id/status/started_at, so the renderer
        # printed `?` for every per-check field).
        status = "pass"
        if not result["ok"]:
            status = "fail"
        elif any(c["status"] == "warn" for c in result["checks"].values()):
            status = "warn"
        # Persist a compact per-check summary (the engine's ontology
        # validator only checks declared required-fields; extra fields
        # ride along untouched).
        check_summary = ",".join(
            f"{name}:{c.get('status', '?')}"
            for name, c in result["checks"].items()
        )
        vid = self.ctx.record("Verification", {
            "research_id": research_id,
            "status": status,
            "started_at": int(time.time()),
            "checks": check_summary,
        })
        self.ctx.link(vid, research_id, "VERIFIES")
        result["verification_id"] = vid
        return result
