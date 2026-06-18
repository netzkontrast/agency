"""novel.manuscript — Manuscript cluster — catalogue coherence, renderers, composite gates, FormatDriver export (Spec 106/107/108/124).

Spec 286 P3 — extracted verbatim from ``novel/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single NovelCapability.
"""
from __future__ import annotations

from agency.capability import verb
from agency.toolresult import ToolResult, Codes
from .._main import (
    CONTENT_WARNINGS,
    _word_tokens,
)


class ManuscriptMixin:
    """Manuscript cluster — catalogue coherence, renderers, composite gates, FormatDriver export (Spec 106/107/108/124)."""

    @verb(role="transform")
    def manuscript_coherence_check(self, novel_id: str) -> ToolResult:
        """Chapter-sequence contiguity check (transform, driver-free).

        Inputs: novel_id.
        Returns: ``{passed, chapter_count, gaps}`` — gaps lists missing
        chapter numbers between 1 and the max present number.
        chain_next: ``novel.render_manuscript`` when contiguous.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        numbers = sorted({int(c.get("number", 0)) for c in chapters})
        gaps: list[int] = []
        if numbers:
            for n in range(1, max(numbers) + 1):
                if n not in numbers:
                    gaps.append(n)
        return ToolResult.success(data={
            "passed": not gaps,
            "chapter_count": len(chapters),
            "gaps": gaps,
        })

    @verb(role="act")
    def render_blurb(self, novel_id: str, hook: str,
                      stakes: str) -> ToolResult:
        """Render a back-cover blurb (act, driver-free).

        Inputs: novel_id, hook (one-sentence premise), stakes.
        Returns: ``{result, artefact}`` blurb artefact.
        chain_next: ``novel.render_query_letter`` for the agent submission.
        """
        node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        title = node.get("title", "Untitled")
        author = node.get("author", "")
        body = (f"**{title}** by {author}\n\n"
                f"{hook}\n\n"
                f"But {stakes}\n")
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "blurb", "novel": novel_id,
                         "title": title, "author": author,
                         "body": body},
        })

    @verb(role="act")
    def render_query_letter(self, novel_id: str, agent_name: str,
                              comp_titles: str = "") -> ToolResult:
        """Render an agent query letter (act, driver-free).

        Inputs: novel_id, agent_name, comp_titles (comparable titles).
        Returns: ``{result, artefact}`` query-letter artefact.
        chain_next: ``novel.render_synopsis`` to bundle the submission.
        """
        node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        title = node.get("title", "Untitled")
        author = node.get("author", "")
        body = (f"Dear {agent_name},\n\n"
                f"I'm seeking representation for my novel "
                f"**{title}**.\n\n"
                f"For fans of {comp_titles}.\n\n"
                f"Sincerely,\n{author}\n")
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "query-letter", "novel": novel_id,
                         "agent": agent_name, "body": body},
        })

    @verb(role="act")
    def render_synopsis(self, novel_id: str) -> ToolResult:
        """Render a synopsis from chapter outline (act, driver-free).

        Inputs: novel_id.
        Returns: ``{result, artefact}`` synopsis artefact with chapters
        in order.
        chain_next: ``novel.render_query_letter`` for the submission.
        """
        node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = sorted(
            self.ctx.neighbors(novel_id, "CHAPTER_OF"),
            key=lambda c: c.get("number", 0))
        title = node.get("title", "Untitled")
        parts = [f"# Synopsis: {title}\n\n"]
        for c in chapters:
            parts.append(
                f"**Chapter {c.get('number', 0)}: {c.get('title', '')}**\n"
                f"{c.get('body', '')[:200]}\n\n")
        body = "".join(parts)
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "synopsis", "novel": novel_id,
                         "chapter_count": len(chapters), "body": body},
        })

    @verb(role="effect")
    def pre_draft_gate(self, novel_id: str) -> ToolResult:
        """Composite gate: storyform + research + chapters present (effect).

        Inputs: novel_id.
        Returns: ``{passed, checks}`` or typed GATE_FAILED.
        chain_next: ``novel.set_novel_status('drafting')`` once passed.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        claims = list(self.ctx.find("NovelClaim"))
        storyforms = [s for s in self.ctx.find("Storyform")
                      if s.get("novel") == novel_id]
        checks = {
            "chapter_outline": bool(chapters),
            "research_present": bool(claims),
            "storyform_present": bool(storyforms),
        }
        if not all(checks.values()):
            failed = [k for k, v in checks.items() if not v]
            return ToolResult.failure(
                Codes.GATE_FAILED,
                f"pre-draft: missing {failed}")
        return ToolResult.success(data={
            "passed": True, "checks": checks,
        })

    @verb(role="effect")
    def beta_ready_gate(self, novel_id: str) -> ToolResult:
        """Composite gate: all chapters drafted+ (effect).

        Passes IFF every Chapter for the Novel has status ∈
        {drafted, revised, final}. Outlined chapters block.

        Inputs: novel_id.
        Returns: ``{passed, checks}`` or typed GATE_FAILED.
        chain_next: ``novel.set_novel_status('beta')`` then ship to readers.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        drafted_plus = {"drafted", "revised", "final"}
        outlined = [c for c in chapters
                    if c.get("status") not in drafted_plus]
        checks = {
            "has_chapters": bool(chapters),
            "all_chapters_drafted": not outlined,
        }
        if not all(checks.values()):
            failed = [k for k, v in checks.items() if not v]
            return ToolResult.failure(
                Codes.GATE_FAILED,
                f"beta-ready: missing {failed}")
        return ToolResult.success(data={
            "passed": True, "checks": checks,
        })

    @verb(role="effect")
    def query_ready_gate(self, novel_id: str) -> ToolResult:
        """Composite gate: status ≥ beta + content-clean (effect).

        Composes: Novel.status reaches {beta, querying, published}
        AND aggregate chapter body passes check_content_warnings
        (empty warnings list).

        Inputs: novel_id.
        Returns: ``{passed, checks}`` or typed GATE_FAILED.
        chain_next: ``novel.render_query_letter`` then agent submission.
        """
        node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        body = " ".join(c.get("body", "") for c in chapters)
        # Re-use the canonical CONTENT_WARNINGS scanner inline (sibling
        # verb composition stays in-process; no MCP roundtrip).
        words_lower = {w.lower() for w in _word_tokens(body)}
        warnings_hit: list[str] = []
        for category, lexicon in CONTENT_WARNINGS.items():
            if words_lower & lexicon:
                warnings_hit.append(category)
        status_ok = node.get("status") in {"beta", "querying", "published"}
        checks = {
            "status_beta_or_later": status_ok,
            "content_clean": not warnings_hit,
        }
        if not all(checks.values()):
            failed = [k for k, v in checks.items() if not v]
            return ToolResult.failure(
                Codes.GATE_FAILED,
                f"query-ready: missing {failed}; warnings={warnings_hit}")
        return ToolResult.success(data={
            "passed": True, "checks": checks,
            "content_warnings": warnings_hit,
        })

    @verb(role="effect")
    def publish_ready_gate(self, novel_id: str) -> ToolResult:
        """Composite gate: contiguous chapters + status ≥ querying (effect).

        Composes: manuscript_coherence_check (no chapter-number gaps)
        AND Novel.status ∈ {querying, published}. The publication-prep
        terminal gate before set_novel_status('published').

        Inputs: novel_id.
        Returns: ``{passed, checks}`` or typed GATE_FAILED.
        chain_next: ``novel.set_novel_status('published')``.
        """
        node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        numbers = sorted(c.get("number") for c in chapters
                         if isinstance(c.get("number"), int))
        gaps: list[int] = []
        if numbers:
            for n in range(1, max(numbers) + 1):
                if n not in numbers:
                    gaps.append(n)
        status_ok = node.get("status") in {"querying", "published"}
        checks = {
            "no_chapter_gaps": not gaps,
            "status_at_querying_or_later": status_ok,
        }
        if not all(checks.values()):
            failed = [k for k, v in checks.items() if not v]
            return ToolResult.failure(
                Codes.GATE_FAILED,
                f"publish-ready: missing {failed}; gaps={gaps}")
        return ToolResult.success(data={
            "passed": True, "checks": checks,
        })

    def _export_format(self, novel_id: str, fmt: str) -> dict:
        novel_node, fail = self._require_novel(novel_id)
        if fail is not None:
            return {"_fail": fail}
        drv = self._maybe_format_driver()
        if drv is None:
            return {"_fail": ToolResult.failure(
                Codes.DEPENDENCY_MISSING,
                "novel_format driver not wired (set engine._novel_production = True "
                "or add the novel_format driver to Engine(drivers=...))")}
        if fmt not in drv.available_formats():
            return {"_fail": ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"format={fmt!r} not in driver.available_formats() "
                f"= {drv.available_formats()}")}
        manuscript_result = self.ctx.call("novel", "render_manuscript",
                                            novel_id=novel_id)
        manuscript_md = (manuscript_result or {}).get("result", "")
        meta = {
            "title": novel_node.get("title", ""),
            "author": novel_node.get("author", ""),
            "genre": novel_node.get("genre", "novel"),
            "slug": novel_node.get("title", "").lower().replace(" ", "-"),
        }
        method = getattr(drv, f"to_{fmt}")
        path = method(manuscript_md, meta)
        aid = self.ctx.record("Artefact", {
            "kind": "published-manuscript",
            "format": fmt, "path": path,
            "novel_id": novel_id,
        })
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        self.ctx.link(self.ctx.intent_id, aid, "PRODUCES")
        return {"format": fmt, "path": path, "artefact_id": aid}

    @verb(role="effect")
    def export_epub(self, novel_id: str) -> ToolResult:
        """Render manuscript + write epub via FormatDriver (effect).

        Inputs: novel_id.
        Returns: ``{format, path, artefact_id}``; typed DEPENDENCY_MISSING
                 when no FormatDriver is wired (production flag off).
        chain_next: ``novel.publication_gate``.
        """
        out = self._export_format(novel_id, "epub")
        if "_fail" in out:
            return out["_fail"]
        return ToolResult.success(data=out)

    @verb(role="effect")
    def export_pdf(self, novel_id: str) -> ToolResult:
        """Render manuscript + write PDF via FormatDriver (effect).

        Inputs: novel_id.
        Returns: ``{format, path, artefact_id}``; typed DEPENDENCY_MISSING
                 when no FormatDriver is wired.
        chain_next: ``novel.publication_gate``.
        """
        out = self._export_format(novel_id, "pdf")
        if "_fail" in out:
            return out["_fail"]
        return ToolResult.success(data=out)

    @verb(role="effect")
    def export_docx(self, novel_id: str) -> ToolResult:
        """Render manuscript + write docx via FormatDriver (effect).

        Inputs: novel_id.
        Returns: ``{format, path, artefact_id}``; typed DEPENDENCY_MISSING
                 when no FormatDriver is wired.
        chain_next: ``novel.publication_gate``.
        """
        out = self._export_format(novel_id, "docx")
        if "_fail" in out:
            return out["_fail"]
        return ToolResult.success(data=out)

    @verb(role="effect")
    def publication_gate(self, novel_id: str) -> ToolResult:
        """Terminal composite: publish_ready + ≥1 export + front-matter declared (effect).

        Composes:
        - ``publish_ready_gate`` (chapters contiguous + status ≥ querying)
        - at least one ``published-manuscript`` Artefact already exists
          (caller has run ``export_epub`` / ``export_pdf`` / ``export_docx``)
        - novel front-matter declares ``content_warnings`` (empty string OK,
          but the field MUST be set so reviewers see a deliberate state).

        Inputs: novel_id.
        Returns: ``{passed, checks, exports: [{format, path}]}`` or typed
                 GATE_FAILED.
        chain_next: terminal — call ``novel.set_novel_status('published')``.
        """
        novel_node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        pub_ready = self.ctx.call("novel", "publish_ready_gate",
                                    novel_id=novel_id)
        ready_passed = bool((pub_ready or {}).get("passed"))
        exports = [
            {"format": a.get("format"), "path": a.get("path")}
            for a in self.ctx.find("Artefact")
            if a.get("kind") == "published-manuscript"
            and a.get("novel_id") == novel_id
        ]
        # `content_warnings` field must be SET (even if empty) — declares
        # the author has thought about it.
        cw_set = "content_warnings" in novel_node
        checks = {
            "publish_ready": ready_passed,
            "has_exports": bool(exports),
            "content_warnings_declared": cw_set,
        }
        if not all(checks.values()):
            return ToolResult.failure(
                Codes.GATE_FAILED,
                f"publication: missing "
                f"{[k for k, v in checks.items() if not v]}")
        return ToolResult.success(data={
            "passed": True, "checks": checks, "exports": exports,
        })
