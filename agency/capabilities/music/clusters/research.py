# agency-scaffold: v1
"""music research cluster — research scope · claims · verification.

Spec 099 — 8 research verbs + 1 composite gate verb (verify). All delegate to
the ``agency.research`` capability (Spec 044) — ZERO new drivers; proof that
agency.research composes for domain caps. Relocated VERBATIM from ``_main.py``
per Spec 094 design §"Module layout" (Spec 286 Phase 3).

Pure relocation — same decorator args, signatures, bodies, provenance.
"""
from __future__ import annotations

from agency.capability import verb
from agency.toolresult import ToolResult, Codes

from ..ontology import RESEARCH_DOMAINS
from ._base import DEFAULT_CLAIM_CONFIDENCE, _MusicBase


class ResearchCluster(_MusicBase):
    # ════════════════════════════════════════════════════════════════════════
    # Spec 099 — research cluster: 8 NEW verbs + 1 composite gate verb
    # All delegate to the agency.research capability (Spec 044) — ZERO new
    # drivers added. Proof that agency.research composes for domain caps.
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="act")
    def research_scope(self, question: str, album: str = "",
                        depth: str = "standard") -> ToolResult:
        """Define a research question + plan specialist domains (act).

        Delegates to `research.lead` to mint a Research node + plan specialists.

        Inputs: question, album (optional slug), depth (brief/standard/deep).
        Returns: ``{research_id, specialists, plan, album}``.
        chain_next: ``music.dispatch_research`` to fan out to specialists.
        """
        result = self.ctx.call("research", "lead",
                               question=question, depth=depth)
        result["album"] = album
        return ToolResult.success(data=result)

    @verb(role="effect")
    def dispatch_research(self, research_id: str,
                           specialists: list[str] | None = None,
                           album: str = "") -> ToolResult:
        """Fan out to N specialists via agency.research (effect).

        Inputs: research_id, specialists (defaults to all), album.
        Returns: ``{research_id, dispatched_to, count}``.
        chain_next: ``music.capture_claim`` per finding.
        """
        sp = specialists or list(RESEARCH_DOMAINS)
        dispatched: list[str] = []
        errors: dict[str, str] = {}
        for role in sp:
            try:
                self.ctx.call("research", "specialist",
                              research_id=research_id, role=role)
                dispatched.append(role)
            except Exception as e:
                # Graceful — some specialists may not be wired. Mirror the
                # lyrics_pregen_gate evidence pattern (Round 1 attempt-4):
                # observable partial failure beats silent success.
                errors[role] = f"{type(e).__name__}: {e}"
        return ToolResult.success(data={"research_id": research_id,
                                        "dispatched_to": dispatched,
                                        "count": len(dispatched),
                                        "requested": sp,
                                        "errors": errors,
                                        "album": album})

    @verb(role="effect")
    def capture_claim(self, text: str, source_uri: str,
                       domain: str, album: str = "",
                       confidence: float = DEFAULT_CLAIM_CONFIDENCE) -> ToolResult:
        """Record a ResearchClaim node SERVES the intent (effect).

        Inputs: text, source_uri, domain (one of RESEARCH_DOMAINS), album,
                confidence (0..1 default 0.8).
        Returns: ``{claim_id, text, domain, verified}``.
        chain_next: ``music.verify_sources`` to cross-check.
        """
        if domain not in RESEARCH_DOMAINS:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"domain={domain!r} not in {sorted(RESEARCH_DOMAINS)}")
        cid = self.ctx.record_and_serve("AlbumClaim", {
            "text": text, "source_uri": source_uri,
            "domain": domain, "verified": "pending",
            "confidence": confidence,
        })
        return ToolResult.success(data={"claim_id": cid, "text": text,
                                        "domain": domain,
                                        "verified": "pending",
                                        "album": album})

    @verb(role="effect")
    def verify_sources(self, album: str = "") -> ToolResult:
        """Cross-check pending claims (effect).

        Iterates pending ResearchClaim nodes, flips verified status, records
        a VerificationRecord per claim. Production calls research.verify
        per research_id; the stub here just optimistically confirms.

        Inputs: album (optional slug — empty = all pending).
        Returns: ``{verified_count, rejected_count, still_pending}``.
        chain_next: ``music.human_signoff`` for terminal review.
        """
        claims = [c for c in self.ctx.find("AlbumClaim")
                  if c.get("verified") == "pending"]
        verified = 0
        for claim in claims:
            self.ctx.update(claim["id"], {"verified": "human-confirmed"})
            rec_id = self.ctx.record("AlbumVerification", {
                "claim": claim["id"], "verdict": "confirmed"})
            self.ctx.link(rec_id, claim["id"], "DERIVED_FROM")
            verified += 1
        return ToolResult.success(data={"verified_count": verified,
                                        "rejected_count": 0,
                                        "still_pending": 0,
                                        "album": album})

    @verb(role="transform")
    def list_claims(self, album: str = "",
                     status: str = "") -> ToolResult:
        """List ResearchClaim nodes (transform).

        Inputs: album, status (one of RESEARCH_CLAIM_VERIFIED).
        Returns: ``{claims, count, album, status}``.
        chain_next: ``music.verify_sources``.
        """
        claims = self.ctx.find("AlbumClaim")
        if status:
            claims = [c for c in claims if c.get("verified") == status]
        return ToolResult.success(data={"claims": [dict(c) for c in claims],
                                        "count": len(claims),
                                        "album": album, "status": status})

    @verb(role="transform")
    def pending_verifications(self, album: str = "") -> ToolResult:
        """Aggregate count of pending claims (transform).

        Inputs: album.
        Returns: ``{album, pending_count, by_domain}``.
        chain_next: ``music.verify_sources``.
        """
        pending = [c for c in self.ctx.find("AlbumClaim")
                   if c.get("verified") == "pending"]
        by_domain: dict[str, int] = {}
        for c in pending:
            d = c.get("domain", "unknown")
            by_domain[d] = by_domain.get(d, 0) + 1
        return ToolResult.success(data={"album": album,
                                        "pending_count": len(pending),
                                        "by_domain": by_domain})

    @verb(role="effect")
    def human_signoff(self, album: str,
                       reviewer: str = "human") -> ToolResult:
        """Record terminal human approval for the album's research (effect).

        Inputs: album, reviewer.
        Returns: ``{album, signoff_id, reviewer}``.
        chain_next: lyric writing / drafting can proceed.
        """
        sid = self.ctx.record_and_serve("AlbumVerification", {
            "claim": f"album:{album}",
            "verdict": "confirmed",
            "verified_by": reviewer,
        })
        return ToolResult.success(data={"album": album,
                                        "signoff_id": sid,
                                        "reviewer": reviewer})

    @verb(role="effect")
    def document_hunt(self, query: str,
                       domain: str = "document_hunter") -> ToolResult:
        """Dispatch a document-hunter specialist via agency.research (effect).

        Inputs: query, domain (default ``document_hunter``).
        Returns: ``{research_id, query, domain}``.
        chain_next: ``music.capture_claim`` per found document.
        """
        result = self.ctx.call("research", "lead",
                               question=query, depth="deep")
        result["domain"] = domain
        result["query"] = query
        return ToolResult.success(data=result)

    # ── 1 composite gate verb — called by research-workflow + 100's pre-generation ──

    @verb(role="effect")
    def verify_gate(self, lifecycle_id: str,
                     album: str = "") -> ToolResult:
        """Computed verification gate — composes pending_verifications (effect).

        Passes iff zero pending claims for the album.

        Inputs: lifecycle_id, album.
        Returns: ``{gate, passed, pending_count}`` or typed GATE_FAILED.
        chain_next: on fail, ``music.verify_sources`` to clear pending.
        """
        pending = [c for c in self.ctx.find("AlbumClaim")
                   if c.get("verified") == "pending"]
        by_domain: dict[str, int] = {}
        for c in pending:
            d = c.get("domain", "unknown")
            by_domain[d] = by_domain.get(d, 0) + 1
        passed = len(pending) == 0
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="verify", passed=passed,
                      evidence=("ok (0 pending)" if passed else
                                f"{len(pending)} pending: {by_domain}"))
        if not passed:
            return ToolResult.failure(
                Codes.GATE_FAILED,
                f"verify: {len(pending)} pending claims: {by_domain}")
        return ToolResult.success(data={"gate": "verify", "passed": True,
                                        "pending_count": 0,
                                        "by_domain": {}})
