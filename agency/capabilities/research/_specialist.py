"""research.specialist — one bounded sub-search per role.

Three roles ship in v1:
  codebase         — grep + AST walk over the repo (confidence 1.0)
  prior-reflections — reflect.recall_semantic (confidence = score)
  doc-corpus       — keyword + semantic match over docs/ (confidence = score)

The `web` role is reserved (Spec 044 line 102) but defers to v2 when
the WebSearchClient injector is non-None. v1 returns an error finding.

Citations are recorded with the rules from Spec 044
§"confidence computation rule".
"""
from __future__ import annotations

import os
import re

from ..._capture import keep_full
from ._findings import semantic_score


_DEFAULT_SEARCH_ROOT = "agency"
_DEFAULT_DOCS_ROOT = "docs"


def _validate_query(query: str) -> dict | None:
    """Reject empty / whitespace-only queries. Without this guard the
    codebase substring matcher's ``"" in line`` is True for every line
    (records arbitrary citations with an empty ``claim_supported``)
    and the doc-corpus substring path has the same hole."""
    if not (query or "").strip():
        return {"citations": 0,
                "summary": "query required (empty / whitespace-only "
                           "would match every line)"}
    return None


def _validate_research_id(memory, research_id: str) -> dict | None:
    """Return an error envelope if ``research_id`` doesn't resolve to a
    ``Research`` node, else ``None``. Checks BOTH existence AND label so
    a caller passing an intent id / citation id by mistake doesn't
    silently anchor citations at a non-Research endpoint (where
    ``research.verify``'s ``MATCH (r:Research)-[:CITES]->…`` query
    can't find them)."""
    if not research_id:
        return {"citations": 0,
                "summary": "research_id required (call research.lead first)"}
    # Spec 056 — label-checked guard via the substrate helper (existence AND
    # Research label). A typo'd intent/citation id no longer anchors citations
    # at a non-Research endpoint that research.verify's MATCH can't find.
    if memory.recall_typed(research_id, "Research") is None:
        return {"citations": 0,
                "summary": f"research_id {research_id!r} is not a valid Research "
                           f"node (call research.lead to mint one)"}
    return None


def run_codebase(memory, ctx, research_id: str, query: str,
                 search_root: str = _DEFAULT_SEARCH_ROOT,
                 max_hits: int = 5) -> dict:
    """Grep search_root for `query`; record one Citation per hit."""
    err = _validate_research_id(memory, research_id) or _validate_query(query)
    if err is not None:
        return err
    if not os.path.isdir(search_root):
        return {"citations": 0, "summary": f"no such root {search_root!r}"}
    hits = []
    for dirpath, dirnames, files in os.walk(search_root):
        dirnames[:] = [d for d in dirnames
                       if d not in {"__pycache__", ".venv", ".git",
                                    ".pytest_cache"}]
        for f in files:
            if not f.endswith(".py"):
                continue
            fp = os.path.join(dirpath, f)
            try:
                with open(fp, encoding="utf-8") as fh:
                    for i, line in enumerate(fh, 1):
                        if query in line:
                            hits.append((fp, i, line.strip()[:200]))
                            if len(hits) >= max_hits:
                                break
            except (OSError, UnicodeDecodeError):
                continue
        if len(hits) >= max_hits:
            break
    for path, line, evidence in hits:
        cit_id = memory.record("Citation", {
            "source_kind": "codebase",
            "source_url_or_path": f"{path}:{line}",
            "evidence_text": evidence,
            "confidence": 1.0,    # Spec 044 §"confidence" — codebase is deterministic
            "claim_supported": query,
            "research_id": research_id,
        })
        memory.link(research_id, cit_id, "CITES")
    return {"citations": len(hits),
            "summary": f"codebase: {len(hits)} hits for {query!r} in {search_root}"}


def run_prior_reflections(memory, ctx, research_id: str, query: str,
                           k: int = 5) -> dict:
    """Call reflect.recall_semantic; record top-k as Citation nodes."""
    err = _validate_research_id(memory, research_id) or _validate_query(query)
    if err is not None:
        return err
    # Invoke via registry so the embedder injector is honoured.
    res, _inv = ctx.registry.invoke(
        memory, ctx.intent_id, "reflect", "recall_semantic",
        agent_id=ctx.agent_id or "agent:research", query=query, k=k)
    results = res.get("results", [])
    for hit in results:
        cit_id = memory.record("Citation", {
            "source_kind": "reflection",
            "source_url_or_path": hit["id"],
            "evidence_text": keep_full(hit["text"], label="reflection evidence"),
            "confidence": float(hit["score"]),    # Spec 044 §"confidence" — uses ranker score
            "claim_supported": query,
            "research_id": research_id,
        })
        memory.link(research_id, cit_id, "CITES")
    return {"citations": len(results),
            "summary": f"prior-reflections: {len(results)} hits for {query!r}"}


def run_doc_corpus(memory, ctx, research_id: str, query: str,
                   docs_root: str = _DEFAULT_DOCS_ROOT,
                   max_hits: int = 5) -> dict:
    """Walk docs_root for files containing query OR semantically close.

    Confidence rule: substring match → 1.0; semantic match only → the
    cosine score.
    """
    err = _validate_research_id(memory, research_id) or _validate_query(query)
    if err is not None:
        return err
    if not os.path.isdir(docs_root):
        return {"citations": 0, "summary": f"no such docs root {docs_root!r}"}
    hits: list[tuple[str, int, str, float]] = []
    embedder = getattr(ctx.registry.engine, "embedder", None) \
        if hasattr(ctx.registry, "engine") and ctx.registry.engine else None
    if embedder is None:
        # Engine attaches itself to registry; fall through with no
        # semantic scoring (substring-only matching).
        pass
    for dirpath, dirnames, files in os.walk(docs_root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for f in files:
            if not f.endswith((".md", ".txt", ".rst")):
                continue
            fp = os.path.join(dirpath, f)
            try:
                with open(fp, encoding="utf-8") as fh:
                    content = fh.read()
            except (OSError, UnicodeDecodeError):
                continue
            # Substring path first.
            for i, line in enumerate(content.splitlines(), 1):
                if query.lower() in line.lower():
                    hits.append((fp, i, line.strip()[:200], 1.0))
                    if len(hits) >= max_hits:
                        break
            if len(hits) >= max_hits:
                break
            # Semantic backup if no substring hits and embedder present.
            # Anchor the snippet at the highest-scoring 200-char window
            # over the file (sliding window step=100) so the recorded
            # citation actually contains evidence the verifier can match
            # — not the file prefix (which the verifier rejects when the
            # supporting text lives deeper in the doc).
            if not any(h[0] == fp for h in hits) and embedder is not None:
                best_score = 0.0
                best_line = 1
                best_snippet = ""
                # Index by line so the citation carries the right line:col.
                lines_with_offsets = []
                pos = 0
                for line_idx, raw_line in enumerate(content.splitlines(True), 1):
                    lines_with_offsets.append((line_idx, pos))
                    pos += len(raw_line)
                # Slide 200-char windows with step 100.
                window = 200
                step = 100
                starts = list(range(0, max(1, len(content) - window + 1), step))
                # Spec 060 round 9 — sliding-window loop skipped the EOF
                # tail when (len - window) wasn't a step multiple. Add an
                # explicit final-window start so a relevant terms in the
                # last chars of a doc still get scored.
                if len(content) > window:
                    tail_start = len(content) - window
                    if tail_start not in starts:
                        starts.append(tail_start)
                elif content and 0 not in starts:
                    starts.append(0)
                for start in starts:
                    chunk = content[start:start + window]
                    if not chunk.strip():
                        continue
                    score = semantic_score(query, chunk, embedder)
                    if score > best_score:
                        best_score = score
                        # Find the line containing this offset.
                        line_no = 1
                        for ln, off in lines_with_offsets:
                            if off > start:
                                break
                            line_no = ln
                        best_line = line_no
                        best_snippet = chunk.strip()
                if best_score >= 0.3:
                    hits.append((fp, best_line, best_snippet, float(best_score)))
        if len(hits) >= max_hits:
            break
    for path, line, evidence, score in hits:
        cit_id = memory.record("Citation", {
            "source_kind": "doc-corpus",
            "source_url_or_path": f"{path}:{line}",
            "evidence_text": evidence,
            "confidence": float(score),
            "claim_supported": query,
            "research_id": research_id,
        })
        memory.link(research_id, cit_id, "CITES")
    return {"citations": len(hits),
            "summary": f"doc-corpus: {len(hits)} hits for {query!r} in {docs_root}"}


def run_web(memory, ctx, research_id: str, query: str,
            web_search=None, k: int = 5) -> dict:
    """Spec 044 §"web specialist" — uses the injected WebSearchClient.

    v1 returns an error if no web_search is injected. v2 may add a
    thin wrapper around the host's `WebSearch` MCP tool.
    """
    err = _validate_research_id(memory, research_id) or _validate_query(query)
    if err is not None:
        return err
    if web_search is None:
        return {
            "citations": 0,
            "summary": "web specialist requires Engine(web_search=…) — "
                       "v1 has no default driver; inject one or use "
                       "another specialist role.",
        }
    results = web_search.search(query, k=k)
    for hit in results:
        # Spec 044 §"confidence" — web baseline 0.9 (URL resolves +
        # text is the page content). v2 may re-fetch to verify.
        cit_id = memory.record("Citation", {
            "source_kind": "web",
            "source_url_or_path": hit.get("url", ""),
            "evidence_text": keep_full(hit.get("text", "") or hit.get("snippet", ""),
                                       label="web evidence"),
            "confidence": 0.9,
            "claim_supported": query,
            "research_id": research_id,
        })
        memory.link(research_id, cit_id, "CITES")
    return {"citations": len(results),
            "summary": f"web: {len(results)} hits for {query!r}"}
