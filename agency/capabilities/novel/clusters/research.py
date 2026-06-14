"""novel.research — Research cluster — claims + xcap research/prompt/thinking integration (Spec 105 + tight-integration).

Spec 286 P3 — extracted verbatim from ``novel/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single NovelCapability.
"""
from __future__ import annotations

from agency.capability import verb
from agency.toolresult import ToolResult
from .._main import (
    CLAIM_VERIFIED,
    RESEARCH_DOMAINS,
)


class ResearchMixin:
    """Research cluster — claims + xcap research/prompt/thinking integration (Spec 105 + tight-integration)."""

    @verb(role="effect", param_enums={"domain": RESEARCH_DOMAINS})
    def capture_claim(self, text: str, source_uri: str,
                       domain: str) -> ToolResult:
        """Record a NovelClaim node SERVING the intent (effect).

        Inputs: text, source_uri, domain (one of ``RESEARCH_DOMAINS``).
        Returns: ``{claim_id, text, domain, verified}``.
        chain_next: ``novel.verify_sources`` (Slice 2) to cross-check.
        """
        if domain not in RESEARCH_DOMAINS:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"domain={domain!r} not in {sorted(RESEARCH_DOMAINS)}")
        cid = self.ctx.record("NovelClaim", {
            "text": text, "source_uri": source_uri,
            "domain": domain, "verified": "pending",
        })
        self.ctx.link(cid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "claim_id": cid, "text": text,
            "domain": domain, "verified": "pending",
        })

    @verb(role="transform")
    def list_claims(self, verified: str = "") -> ToolResult:
        """List captured claims; optional verified-status filter (transform).

        Inputs: verified (one of ``CLAIM_VERIFIED`` or ``""`` for all).
        Returns: ``{claims, count}``.
        chain_next: ``novel.verify_sources`` for pending claims.
        """
        if verified and verified not in CLAIM_VERIFIED:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"verified={verified!r} not in {sorted(CLAIM_VERIFIED)}")
        claims = [c for c in self.ctx.find("NovelClaim")
                  if not verified or c.get("verified") == verified]
        return ToolResult.success(data={
            "claims": claims, "count": len(claims),
        })

    @verb(role="transform")
    def pending_verifications(self) -> ToolResult:
        """Aggregate pending claims by domain (transform).

        Inputs: none.
        Returns: ``{count, by_domain}`` — only claims with ``verified=="pending"``.
        chain_next: ``novel.dispatch_research`` (Slice 2) to fan out specialists.
        """
        pending = [c for c in self.ctx.find("NovelClaim")
                   if c.get("verified") == "pending"]
        by_domain: dict[str, int] = {}
        for c in pending:
            d = c.get("domain", "unknown")
            by_domain[d] = by_domain.get(d, 0) + 1
        return ToolResult.success(data={
            "count": len(pending), "by_domain": by_domain,
        })

    @verb(role="effect")
    def dispatch_novel_research(self, question: str,
                                  domain: str) -> ToolResult:
        """Mint a research lead + record NovelClaim (delegates to research cap).

        Routes through ``research.lead`` to mint the Research node, then
        binds the resulting research_id into a NovelClaim that SERVES
        the novel's intent. domain must be one of ``RESEARCH_DOMAINS``.

        Inputs: question, domain (one of RESEARCH_DOMAINS).
        Returns: ``{research_id, claim_id, question, domain}``.
        chain_next: ``research.specialist`` per domain or ``novel.verify_sources``.
        """
        if domain not in RESEARCH_DOMAINS:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"domain={domain!r} not in {sorted(RESEARCH_DOMAINS)}")
        # Cross-cap call — research.lead mints the Research node + serves
        # the current intent. The Invocation+SERVES edge is auto-recorded
        # by Registry.invoke.
        lead = self.ctx.call("research", "lead",
                              question=question, depth="standard")
        research_id = (lead or {}).get("research_id", "")
        # Bind into NovelClaim so the novel cap's provenance traversal
        # surfaces the delegation.
        cid = self.ctx.record("NovelClaim", {
            "text": question, "source_uri": research_id,
            "domain": domain,
        })
        self.ctx.link(cid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "research_id": research_id, "claim_id": cid,
            "question": question, "domain": domain,
        })

    @verb(role="act")
    def render_chapter_brief(self, chapter_id: str,
                               research_intent_id: str = "") -> ToolResult:
        """Produce a research-dossier brief tied to a chapter (act, xcap to prompt).

        Gathers chapter context (parent novel title, chapter title + body
        preview) and renders a research-dossier artefact. When
        ``research_intent_id`` is supplied, chains ``prompt.brief_render``
        to weave the dossier into the body; otherwise renders a minimal
        body from chapter context alone.

        Inputs: chapter_id, research_intent_id (optional).
        Returns: ``{result, artefact}`` research-dossier.
        chain_next: ``novel.dispatch_novel_research`` if more sources needed.
        """
        _, fail = self._require_chapter(chapter_id)
        if fail is not None:
            return fail
        chapter = self.ctx.recall(chapter_id) or {}
        novel_id = chapter.get("novel", "")
        novel = self.ctx.recall(novel_id) or {}
        title = novel.get("title", "Untitled")
        cnum = chapter.get("number", 0)
        ctitle = chapter.get("title", "")
        body_preview = (chapter.get("body") or "")[:300]
        # Cross-cap call when an upstream research intent is available;
        # otherwise render context-only.
        prompt_body = ""
        if research_intent_id:
            try:
                pr = self.ctx.call("prompt", "brief_render",
                                    research_intent_id=research_intent_id)
                if isinstance(pr, dict):
                    prompt_body = pr.get("body", "")
            except Exception:
                # Best-effort — degrade to context-only brief.
                prompt_body = ""
        body = (
            f"# Research Dossier — {title}, Chapter {cnum}: {ctitle}\n\n"
            f"## Chapter context (preview)\n{body_preview}\n\n"
            f"## Research findings\n{prompt_body or '_(none yet — call dispatch_novel_research)_'}\n"
        )
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "research-dossier",
                          "chapter": chapter_id, "novel": novel_id,
                          "body": body},
        })

    @verb(role="act")
    def storyform_critical_pass(self, novel_id: str) -> ToolResult:
        """Critical-thinking pass over the storyform (act, xcap to thinking).

        Walks ``thinking.apply_full_review`` against the novel's storyform
        body (or premise / title as fallback) and surfaces the 8-method
        scaffold as a thinking-analysis artefact. The xcap call records
        a SERVES edge from the thinking cap's Invocation back to this
        intent — provenance traversal sees the critique.

        Inputs: novel_id.
        Returns: ``{result, artefact}`` thinking-analysis.
        chain_next: revise storyform per the surfaced concerns.
        """
        node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        # Build the subject from the most-specific available signal.
        storyforms = [s for s in self.ctx.find("Storyform")
                      if s.get("novel") == novel_id]
        subject = (storyforms[0].get("body") if storyforms
                    and storyforms[0].get("body")
                    else f"Novel: {node.get('title','')} by {node.get('author','')}")
        # Cross-cap call — thinking.apply_full_review serves the same intent.
        tr = self.ctx.call("thinking", "apply_full_review",
                            subject=subject, depth="standard")
        body = (tr or {}).get("result") or (tr or {}).get("body") or str(tr or "")
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "thinking-analysis",
                          "novel": novel_id, "body": body},
        })

    @verb(role="effect")
    def record_storyform_decision(self, novel_id: str, decision: str,
                                    rationale: str = "") -> ToolResult:
        """Record a contested storyform decision (effect, xcap to dogfood).

        Routes through ``dogfood.record_decision`` so the decision lands
        in the cluster-wide decision audit. ``subject`` is bound to the
        novel id so analyses can filter by story.

        Inputs: novel_id, decision, rationale (optional).
        Returns: ``{novel_id, decision_id, decision}``.
        chain_next: continue authoring; later ``analyze.graph`` reads
                    the audit trail.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        result = self.ctx.call("dogfood", "record_decision",
                                subject=novel_id,
                                decision=decision,
                                rationale=rationale)
        decision_id = (result or {}).get("decision_id", "")
        return ToolResult.success(data={
            "novel_id": novel_id,
            "decision_id": decision_id,
            "decision": decision,
        })
