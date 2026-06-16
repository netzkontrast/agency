# agency-scaffold: v1
"""document — graph-native rendering + briefing (Spec 043).

Document renders graph-native briefings: an index of a repo, an explanation of a subsystem, or a markdown rendering produced on demand from the graph.

Use when: a repository's structure must be understood or rendered — an explanation of a subsystem, a project index, or a graph-native rendering — without loading the whole tree.
Triggers:
- An unfamiliar codebase that needs onboarding
- A stale mental model of a tree untouched for weeks
- A subsystem whose purpose is unclear from the files alone
Red flags:
- Reading every file to grasp a repo → index it via capability_document_index_repo
- Guessing a subsystem's role → get capability_document_explain output
"""
from __future__ import annotations

import os
import time

from agency.capability import (
    ArtefactSchemas, CapabilityBase, RenderTemplates, verb,
)
from agency.ontology import OntologyExtension

from . import _explain, _index_repo, _interconnect, _render


_REPO_BRIEFING_SKILL = {
    "name": "repo-briefing",
    "kind": "discipline",
    "phases": [
        {"index": 1, "name": "scope", "produces": ["path", "max_tokens"]},
        {"index": 2, "name": "scan", "produces": ["index_id", "tokens"]},
        {"index": 3, "name": "render", "produces": ["content"]},
        {"index": 4, "name": "publish", "produces": ["written"], "gate": "hard"},
    ],
}


_SUPPORTED_SCOPES = frozenset({
    "install-artefacts", "reflections", "provenance", "capability-catalogue",
    "research-report",
})




class DocumentCapability(CapabilityBase):
    name = "document"
    home = "memory"
    render_templates = RenderTemplates.from_module(__file__)
    artefact_schemas = ArtefactSchemas.from_module(__file__)
    ontology = OntologyExtension(
        nodes={
            "RepoIndex": ["path", "content_sha", "token_count", "generated_at"],
            # Spec 292 — the Document is the universal convergence artefact:
            # a file's stable identity, bi-directionally interconnected with the
            # graph. Optional props bind the OTHER substrate layers onto it —
            # `template` (the generator), `schema` (the structural contract) —
            # so a Document is where datalayer · templates · schemas · ontology ·
            # prompt all come together. Required = identity (path) + integrity.
            "Document":    ["path", "content_sha"],
            # An append-only revision; `source` tags graph- vs file-authored so
            # both coexist (keep-both, bi-temporal — latest recorded_at wins).
            "DocRevision": ["source", "content_sha"],
        },
        edges={
            "INDEXES",
            "REVISION_OF",   # DocRevision → Document (append-only history)
            "CONFORMS_TO",   # Document    → Schema   (datalayer/schema binding)
        },
        enums={("DocRevision", "source"): {"graph", "file"}},
        # Spec 060: `explanation` schema migrated to
        # `document/schemas/explanation.json`. `repo-index` stays as
        # a dict declaration because no file-form exists yet.
        schemas={
            "repo-index": {"name": "repo-index",
                           "required": ["path", "content_sha", "token_count"]},
        },
        skills={"repo-briefing": _REPO_BRIEFING_SKILL},
    )

    @verb(role="transform")
    def render(self, scope: str, for_intent_id: str = "",
               format: str = "markdown") -> dict:
        """Project graph state to markdown; deterministic.

        Inputs: scope (str — one of install-artefacts | reflections |
                provenance | capability-catalogue),
                for_intent_id (str — required for provenance, optional
                filter for reflections; named `for_intent_id` rather
                than `intent_id` because the substrate already injects
                intent_id for SERVES discipline),
                format (str — 'markdown' in v1).
        Returns: ``{content, tokens, node_count, scope}``.
        chain_next: caller writes to disk — and a disk edit round-trips back
        via ``document.ingest`` (graph↔file are peers now; Spec 292).
        """
        if format != "markdown":
            return {"content": "", "tokens": 0, "node_count": 0, "scope": scope,
                    "error": f"format={format!r} not supported in v1"}
        if scope not in _SUPPORTED_SCOPES:
            return {"content": "", "tokens": 0, "node_count": 0, "scope": scope,
                    "error": f"unknown scope {scope!r}; supported: "
                             f"{sorted(_SUPPORTED_SCOPES)}"}
        memory = self.ctx.memory
        # Spec 056 — label-check a supplied for_intent_id, but the EXPECTED label
        # is scope-dependent: provenance/reflections scope it to an Intent, while
        # research-report forwards it to render_research_report AS a Research id
        # (research.lead's output). An Intent-only guard would reject the valid
        # deep-research publish path (PR #22 review).
        if for_intent_id:
            if (scope in ("provenance", "reflections")
                    and memory.recall_typed(for_intent_id, "Intent") is None):
                return {"content": "", "tokens": 0, "node_count": 0, "scope": scope,
                        "error": f"for_intent_id {for_intent_id!r} is not an Intent id"}
            if (scope == "research-report"
                    and memory.recall_typed(for_intent_id, "Research") is None):
                return {"content": "", "tokens": 0, "node_count": 0, "scope": scope,
                        "error": f"for_intent_id {for_intent_id!r} is not a Research id"}
        if scope == "install-artefacts":
            content, node_count = _render.render_install_artefacts(memory)
        elif scope == "reflections":
            content, node_count = _render.render_reflections(memory, for_intent_id)
        elif scope == "provenance":
            content, node_count = _render.render_provenance(memory, for_intent_id)
        elif scope == "capability-catalogue":
            content, node_count = _render.render_capability_catalogue(self.ctx.registry)
        else:  # research-report — Spec 044 §"Render"
            content, node_count = _render.render_research_report(memory, for_intent_id)
        return {
            "content": content,
            "tokens": _explain._count_tokens(content),
            "node_count": node_count,
            "scope": scope,
        }

    @verb(role="act")
    def explain(self, target: str, depth: str = "standard") -> dict:
        """Deterministic code → markdown explanation; emits a Reflection.

        Inputs: target (str — file path | module | module.symbol),
                depth (str — brief | standard | deep).
        Returns: ``{reflection_id, content, tokens}``.
        chain_next: caller renders or stores the content.
        """
        if depth not in _explain._DEPTH_BUDGETS:
            depth = "standard"
        try:
            out = _explain.explain(target, depth=depth)
        except (ValueError, FileNotFoundError) as exc:
            return {"error": str(exc), "target": target, "depth": depth}
        rid = self.ctx.record_and_serve("Reflection", {
            "scope": "technical",
            "kind": "explanation",
            "target": target,
            "depth": depth,
            "text": out["content"],
        })
        # Parity with reflect.note: also link OBSERVED_DURING so the
        # explanation surfaces in intent-scoped reflection views
        # (document.render(scope='reflections', for_intent_id=...) +
        # document.index_repo's recent-activity filter).
        self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
        return {
            "reflection_id": rid,
            "content": out["content"],
            "tokens": out["tokens"],
        }

    @verb(role="effect")
    def index_repo(self, path: str = ".", apply: bool = False,
                   max_tokens: int = 3000) -> dict:
        """94%-reduction repo briefing — deterministic; ≤ max_tokens.

        Inputs: path (str), apply (bool — write PROJECT_INDEX.md),
                max_tokens (int — budget; default 3000).
        Returns: ``{index_id, content, tokens, files_scanned, writeup}``.
        chain_next: caller publishes via ``apply=True`` after review.
        """
        content, tokens, files_scanned = _index_repo.render(
            path, self.ctx.memory, intent_id=self.ctx.intent_id,
            max_tokens=max_tokens)
        sha = _index_repo.content_sha(content)
        index_id = self.ctx.record_and_serve("RepoIndex", {
            "path": os.path.abspath(path),
            "content_sha": sha,
            "token_count": tokens,
            "generated_at": int(time.time()),
        })
        writeup = "planning-only"
        if apply:
            target = os.path.join(os.path.abspath(path), "PROJECT_INDEX.md")
            try:
                with open(target, "w", encoding="utf-8") as f:
                    f.write(content)
                writeup = f"wrote {target}"
            except OSError as exc:
                writeup = f"write failed: {exc}"
        return {
            "index_id": index_id,
            "content": content,
            "tokens": tokens,
            "files_scanned": files_scanned,
            "writeup": writeup,
        }

    # ── Spec 292 — graph↔markdown interconnect (bi-directional round-trip) ─────

    def _doc_revisions(self, document_id: str) -> list[dict]:
        """Revisions of a Document, latest-recorded first (keep-both read)."""
        revs = self.ctx.neighbors(document_id, "REVISION_OF", direction="in")
        return sorted(revs, key=lambda r: r.get("recorded_at", 0), reverse=True)

    def _append_revision(self, document_id: str, *, source: str, sha: str,
                         body: str, clarity_score: int | None) -> str:
        """Append an append-only DocRevision REVISION_OF the Document."""
        prior = self._doc_revisions(document_id)
        next_tick = max((r.get("recorded_at", 0) for r in prior), default=0) + 1
        props = {"source": source, "content_sha": sha, "text": body,
                 "recorded_at": next_tick}
        if clarity_score is not None:
            props["clarity_score"] = clarity_score
        rev_id = self.ctx.record_and_serve("DocRevision", props,
                                           parent=document_id, edge="REVISION_OF")
        return rev_id

    def _audit_as_prompt(self, body: str) -> int | None:
        """Spec 292 — every file is also a prompt: score the body via prompt.audit.
        Best-effort (xcap); never fails the ingest if the prompt cap is absent."""
        try:
            res = self.ctx.call("prompt", "audit", prompt_body=body)
        except Exception:                                       # noqa: BLE001
            return None
        score = (res or {}).get("clarity_score") if isinstance(res, dict) else None
        return score if isinstance(score, int) else None

    @verb(role="effect")
    def ingest(self, path: str, audit: bool = True,
               template: str = "", schema: str = "") -> dict:
        """Round-trip a markdown file INTO the graph (file → graph; Spec 292).

        Inverts the old premise (files were a one-way rendered view): an
        edited markdown file is now an editable PEER that flows back into the
        graph as an append-only ``DocRevision``. Keep-both, bi-temporal: the
        prior (graph- or file-authored) version is retained; latest wins on
        read. An un-anchored file mints a ``Document`` and the stable
        ``<!-- agency-node: … -->`` anchor is written back. Every file is also
        a prompt — the body is scored via ``prompt.audit`` (``audit=True``).
        ``template`` / ``schema`` bind the other substrate layers onto the
        Document (convergence artefact).

        Inputs: path (str — the .md file), audit (bool — prompt-audit the body),
                template (str — generator binding), schema (str — schema binding).
        Returns: ``{document_id, revision_id, action, content_sha, anchored,
                   clarity_score, path}``. action ∈ created | revised | unchanged.
        chain_next: ``document.revisions`` to read the keep-both history.
        """
        try:
            with open(path, encoding="utf-8") as f:
                raw = f.read()
        except OSError as exc:
            return {"error": f"cannot read {path!r}: {exc}", "path": path}

        anchor_id, body = _interconnect.extract_anchor(raw)
        sha = _interconnect.content_sha(body)
        doc_props = {"path": os.path.abspath(path), "content_sha": sha}
        if template:
            doc_props["template"] = template
        if schema:
            doc_props["schema"] = schema

        existing = self.ctx.recall_typed(anchor_id, "Document") if anchor_id else None
        clarity = self._audit_as_prompt(body) if audit else None

        if existing is None:
            # Mint a Document and stamp the stable anchor back into the file.
            document_id = self.ctx.record_and_serve("Document", doc_props)
            if schema:
                self.ctx.link(document_id, f"schema:{schema}", "CONFORMS_TO")
            with open(path, "w", encoding="utf-8") as f:
                f.write(_interconnect.stamp_anchor(body, document_id))
            rev_id = self._append_revision(document_id, source="file", sha=sha,
                                           body=body, clarity_score=clarity)
            return {"document_id": document_id, "revision_id": rev_id,
                    "action": "created", "content_sha": sha, "anchored": True,
                    "clarity_score": clarity, "path": doc_props["path"]}

        document_id = anchor_id
        if existing.get("content_sha") == sha:
            return {"document_id": document_id, "revision_id": "",
                    "action": "unchanged", "content_sha": sha, "anchored": True,
                    "clarity_score": clarity, "path": doc_props["path"]}

        rev_id = self._append_revision(document_id, source="file", sha=sha,
                                       body=body, clarity_score=clarity)
        self.ctx.update(document_id, doc_props)
        return {"document_id": document_id, "revision_id": rev_id,
                "action": "revised", "content_sha": sha, "anchored": True,
                "clarity_score": clarity, "path": doc_props["path"]}

    @verb(role="effect")
    def sync(self, path: str = ".", audit: bool = True) -> dict:
        """Ingest every CHANGED markdown file under ``path`` (Spec 292).

        The batch, idempotent entry point — the hook target for the
        ``document.sync`` pre-commit step (verb-now, hook-later). A file path
        ingests that one file; a directory walks ``**/*.md``. Unchanged files
        (``action == 'unchanged'``) are skipped.

        Inputs: path (str — file or directory), audit (bool).
        Returns: ``{root, ingested: [...], skipped: [...]}``.
        chain_next: commit the round-tripped graph state.
        """
        root = os.path.abspath(path)
        if os.path.isfile(root):
            targets = [root]
        else:
            targets = [os.path.join(d, fn)
                       for d, _, files in os.walk(root)
                       for fn in sorted(files) if fn.endswith(".md")]
        ingested, skipped = [], []
        for t in sorted(targets):
            r = self.ingest(t, audit=audit)
            if r.get("action") in ("created", "revised"):
                ingested.append({"path": t, "document_id": r.get("document_id"),
                                 "action": r["action"]})
            else:
                skipped.append({"path": t, "reason": r.get("action") or r.get("error")})
        return {"root": root, "ingested": ingested, "skipped": skipped}

    @verb(role="act")
    def revisions(self, document_id: str) -> dict:
        """Read a Document's keep-both revision history (Spec 292).

        Proves the bi-temporal keep-both contract: every ingest/render appends
        a revision; nothing is overwritten. ``latest`` is the newest by
        ``recorded_at``; ``history`` is latest-first.

        Inputs: document_id (str).
        Returns: ``{document_id, count, latest, history}``.
        chain_next: ``document.render`` to re-project, or diff sources.
        """
        if self.ctx.recall_typed(document_id, "Document") is None:
            return {"error": f"{document_id!r} is not a Document id",
                    "document_id": document_id, "count": 0, "history": []}
        history = self._doc_revisions(document_id)
        return {"document_id": document_id, "count": len(history),
                "latest": history[0] if history else None, "history": history}

    def _sessions_dir(self) -> str:
        """The dedicated directory for past-session Documents — sibling of the
        graph DB (so the real engine archives into ``.agency/sessions/``)."""
        base = os.path.abspath(".agency")
        try:
            conn = self.ctx.memory.g._conn
            conn = getattr(conn, "sqlite_connection", conn)
            for _seq, name, dbfile in conn.execute("PRAGMA database_list").fetchall():
                if name == "main" and dbfile:
                    base = os.path.dirname(os.path.abspath(dbfile))
                    break
        except Exception:                                       # noqa: BLE001
            pass
        return os.path.join(base, "sessions")

    @verb(role="effect")
    def session(self, for_intent_id: str = "", apply_path: str = "",
                archive: bool = True) -> dict:
        """Render a Session as a Document — the four concepts converge (Spec 292).

        A Session Document gathers the substrate's four concepts under one
        artefact: **Intent** (the why/what/accept), **Capability** (the
        Invocations that served it), **Lifecycle** (the Lifecycle/skill phases
        walked), and **Memory** (the Reflections recorded). This is what
        "Documents are the artefact in which everything comes together" means
        concretely. The render is graph-authored (``source='graph'``) and, when
        archived/applied, written to disk with a stable anchor so it round-trips
        back via ``document.ingest`` — closing the bi-directional loop.

        ``archive=True`` (default) deposits the Document into the dedicated
        **past-sessions directory** (``<db-dir>/sessions/<intent>.md``, i.e.
        ``.agency/sessions/`` for the real engine), so every session is a
        durable, round-trippable artefact. ``apply_path`` overrides the location.

        Inputs: for_intent_id (str — defaults to the serving Intent),
                apply_path (str — explicit .md path; overrides archive),
                archive (bool — write into the past-sessions directory).
        Returns: ``{document_id, content, tokens, sections, written}``.
        chain_next: ``document.ingest`` the written file to round-trip edits.
        """
        intent_id = for_intent_id or self.ctx.intent_id
        intent = self.ctx.recall_typed(intent_id, "Intent")
        if intent is None:
            return {"error": f"{intent_id!r} is not an Intent id",
                    "intent_id": intent_id}

        invocations = self.ctx.nodes_serving(intent_id, "Invocation")
        lifecycles = self.ctx.nodes_serving(intent_id, "Lifecycle")
        reflections_md, refl_n = _render.render_reflections(self.ctx.memory, intent_id)

        caps: dict[str, int] = {}
        for inv in invocations:
            key = f"{inv.get('capability', '?')}.{inv.get('verb', '?')}"
            caps[key] = caps.get(key, 0) + 1

        lines = [
            f"# Session — {intent_id}",
            "",
            "## Intent",
            f"- **purpose**: {intent.get('purpose', '')}",
            f"- **deliverable**: {intent.get('deliverable', '')}",
            f"- **acceptance**: {intent.get('acceptance', '')}",
            "",
            "## Capability",
            f"_{len(invocations)} invocation(s) across {len(caps)} verb(s)_",
        ]
        lines += [f"- `{k}` ×{n}" for k, n in sorted(caps.items())] or ["- (none)"]
        lines += [
            "",
            "## Lifecycle",
            f"_{len(lifecycles)} lifecycle(s)_",
        ]
        lines += [f"- {lc.get('state', '?')} @ {lc.get('phase', '?')}"
                  for lc in lifecycles] or ["- (none)"]
        lines += ["", "## Memory", reflections_md or "_(no reflections)_", ""]
        content = "\n".join(lines)

        # Resolve the on-disk home: explicit apply_path wins, else the dedicated
        # past-sessions directory when archiving.
        target = ""
        if apply_path:
            target = os.path.abspath(apply_path)
        elif archive:
            target = os.path.join(self._sessions_dir(),
                                  f"{intent_id.replace(':', '_')}.md")

        document_id = self.ctx.record_and_serve("Document", {
            "path": target or f"session:{intent_id}",
            "content_sha": _interconnect.content_sha(content)})
        self._append_revision(document_id, source="graph",
                              sha=_interconnect.content_sha(content),
                              body=content, clarity_score=None)

        written = ""
        if target:
            try:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "w", encoding="utf-8") as f:
                    f.write(_interconnect.stamp_anchor(content, document_id))
                written = target
            except OSError as exc:
                written = f"write failed: {exc}"

        return {"document_id": document_id, "content": content,
                "tokens": _explain._count_tokens(content),
                "sections": ["Intent", "Capability", "Lifecycle", "Memory"],
                "written": written}
