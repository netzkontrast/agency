# agency-scaffold: v1
"""research — lead + specialists + verifier (Spec 044).

Research runs a question through a lead that scopes it, specialists that gather evidence, and a verifier that adversarially checks claims before publishing.

Use when: an open question needs cited evidence from multiple sources — driving a research question through a lead, fan-out specialists, and an adversarial verifier.
Triggers:
- A question whose answer needs cited, cross-checked sources
- A claim that should be verified before it is trusted
- A topic too broad for a single lookup
Red flags:
- Trusting a single source → cross-check with capability_research_verify
- Answering an open question from memory → run capability_research_lead
"""
from __future__ import annotations

import re
import time

from agency.capability import (
    ArtefactSchemas, CapabilityBase, RenderTemplates, verb,
)
from agency.ontology import OntologyExtension

from . import _lead, _specialist, _verify


# Spec 126 — Google Drive source resolution.
# A valid Google Drive file_id is the URL-safe base64 alphabet; we accept
# [A-Za-z0-9_-]{20,} so a stray space / non-id string fails INVALID_SOURCE
# rather than silently becoming the "file_id".
_GDOC_FILE_ID_RE = re.compile(r"[A-Za-z0-9_-]{20,}")
_GDOC_URL_HOSTS = ("docs.google.com", "drive.google.com")


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
    home = "intent"
    render_templates = RenderTemplates.from_module(__file__)
    artefact_schemas = ArtefactSchemas.from_module(__file__)
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
        # PR review round 8 (r_research_status): roll the verdict back
        # onto the Research node so downstream workflows that filter for
        # `ready`/`blocked` see the verification outcome, not the stale
        # `planning` status that `lead` wrote. The status enum
        # (_RESEARCH_STATUSES) carries: planning, in-progress, ready,
        # blocked. Map pass→ready, warn→ready (advisory), fail→blocked.
        new_status = "ready" if status in ("pass", "warn") else "blocked"
        try:
            self.ctx.memory.update(research_id, {"status": new_status})
        except (KeyError, ValueError):
            # The Research node was already superseded mid-verify, or
            # the ontology rejected the update — neither is fatal here;
            # the Verification node still captures the verdict.
            pass
        result["verification_id"] = vid
        return result

    # ------------------------------------------------------------------
    # Spec 126 — Google Drive ingest (subagent-isolated; no body in main ctx).
    # ------------------------------------------------------------------

    @verb(role="transform")
    def ingest_gdoc(self, source: str, dest: str = "") -> dict:
        """Compose a subagent dispatch contract that ingests a Google Doc to disk.

        The verb performs NO I/O. It resolves ``source`` (URL or file_id) and
        returns a contract the orchestrator hands to the Agent tool: the
        subagent fetches via ``mcp__Google_Drive__*``, writes to ``dest``, and
        returns ONLY ``{path, bytes, lines, sha256, title}`` — the doc body
        never crosses back to main context. After the subagent returns, call
        ``research.record_ingested_source`` with the metadata to record the
        ``ingested-source`` Artefact (SERVES + PRODUCES edges).

        Inputs: source (URL or file_id), dest (str — default
                ``.agency/sources/gdoc-<id>.md``).
        Returns: ``{action, prompt, tools, model, dest, file_id, after}``
                 OR ``{error: 'INVALID_SOURCE', source}``.
        chain_next: orchestrator dispatches Agent tool with ``prompt``+``tools``;
                    on return, calls ``after.verb`` with ``after.kwargs``
                    plus the subagent's structured return.
        """
        fid = _resolve_gdoc_id(source)
        if not fid:
            return {"error": "INVALID_SOURCE", "source": source}
        dest = dest or f".agency/sources/gdoc-{fid}.md"
        source_url = (source if source.startswith("http")
                      else f"https://docs.google.com/document/d/{fid}/edit")
        prompt = _gdoc_subagent_prompt(fid, dest)
        return {
            "action": "dispatch_subagent",
            "prompt": prompt,
            "tools": [
                "mcp__Google_Drive__download_file_content",
                "mcp__Google_Drive__get_file_metadata",
                "Write",
                "Bash",
            ],
            "model": "haiku",
            "dest": dest,
            "file_id": fid,
            "after": {
                "verb": "research.record_ingested_source",
                "kwargs": {
                    "intent_id": self.ctx.intent_id,
                    "source_url": source_url,
                    "dest": dest,
                },
            },
        }

    @verb(role="effect")
    def record_ingested_source(self, source_url: str, dest: str,
                               bytes: int, lines: int, sha256: str,
                               title: str) -> dict:
        """Record an ``ingested-source`` Artefact (SERVES intent + PRODUCES edge).

        Idempotent on ``(intent_id, sha256)``: a re-fetch of the same doc body
        returns the existing artefact_id, so a re-run of an ingestion pipeline
        doesn't double-record.

        Inputs: source_url (str — gdoc URL), dest (str — path on disk),
                bytes/lines (int), sha256 (str — 64 hex), title (str).
        Returns: ``{artefact_id, idempotent}`` OR
                 ``{error: 'UNKNOWN_INTENT', intent_id}``.
        chain_next: ``analyze.graph`` to see the corpus; downstream readers
                    open ``dest`` directly.
        """
        iid = self.ctx.intent_id
        existing = self._find_ingested_source(iid, sha256)
        if existing:
            return {"artefact_id": existing, "idempotent": True}

        aid = self.ctx.record("Artefact", {
            "kind": "ingested-source",
            "source_url": source_url,
            "path": dest,
            "bytes": int(bytes),
            "lines": int(lines),
            "sha256": sha256,
            "title": title,
        })
        self.ctx.link(aid, iid, "SERVES")
        self.ctx.link(iid, aid, "PRODUCES")
        return {"artefact_id": aid, "idempotent": False}

    def _find_ingested_source(self, intent_id: str, sha256: str) -> str | None:
        rows = self.ctx.memory.g.query(
            "MATCH (i:Intent)-[:PRODUCES]->(a:Artefact) "
            "WHERE i.id = $iid AND a.kind = 'ingested-source' "
            "AND a.sha256 = $sha RETURN a",
            {"iid": intent_id, "sha": sha256})
        if not rows:
            return None
        # graphqlite's row["a"]["id"] is its internal int; the agency-level
        # node id lives in properties["id"] (see _checks.py:59 comment).
        return rows[0]["a"]["properties"].get("id")


def _resolve_gdoc_id(source: str) -> str | None:
    """URL → file_id, or bare file_id → file_id, or None."""
    if not source or not isinstance(source, str):
        return None
    source = source.strip()
    if source.startswith("http"):
        # docs.google.com/document/d/<ID>/... or drive.google.com/file/d/<ID>/...
        if not any(h in source for h in _GDOC_URL_HOSTS):
            return None
        m = re.search(r"/d/([A-Za-z0-9_-]{20,})", source)
        return m.group(1) if m else None
    # Bare id — must be the URL-safe base64 alphabet end-to-end.
    if _GDOC_FILE_ID_RE.fullmatch(source):
        return source
    return None


def _gdoc_subagent_prompt(file_id: str, dest: str) -> str:
    return (
        f"Ingest Google Doc file_id={file_id} to {dest}. Steps:\n"
        f"1. Call mcp__Google_Drive__download_file_content with file_id={file_id} "
        f"and mimeType=\"text/markdown\".\n"
        f"2. Write the returned body to {dest} using the Write tool.\n"
        f"3. Run Bash: shasum -a 256 {dest} | awk '{{print $1}}' (capture SHA);\n"
        f"   wc -l < {dest} (capture lines); wc -c < {dest} (capture bytes).\n"
        f"4. Call mcp__Google_Drive__get_file_metadata with file_id={file_id} "
        f"to capture the title (name field).\n"
        f"5. Return EXACTLY ONE JSON line and nothing else:\n"
        f'   {{"path": "{dest}", "bytes": N, "lines": N, "sha256": "...", "title": "..."}}\n'
        f"\n"
        f"HARD CONSTRAINT: Do not echo or summarise the document body. The body lives on disk; "
        f"only the metadata JSON crosses back to the orchestrator. Do not output the body at "
        f"any point, in any form, even partially."
    )
