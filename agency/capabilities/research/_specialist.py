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

from ._findings import semantic_score


_DEFAULT_SEARCH_ROOT = "agency"
_DEFAULT_DOCS_ROOT = "docs"


def run_codebase(memory, ctx, research_id: str, query: str,
                 search_root: str = _DEFAULT_SEARCH_ROOT,
                 max_hits: int = 5) -> dict:
    """Grep search_root for `query`; record one Citation per hit."""
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
    # Invoke via registry so the embedder injector is honoured.
    res, _inv = ctx.registry.invoke(
        memory, ctx.intent_id, "reflect", "recall_semantic",
        agent_id=ctx.agent_id or "agent:research", query=query, k=k)
    results = res.get("results", [])
    for hit in results:
        cit_id = memory.record("Citation", {
            "source_kind": "reflection",
            "source_url_or_path": hit["id"],
            "evidence_text": hit["text"][:200],
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
            if not any(h[0] == fp for h in hits) and embedder is not None:
                score = semantic_score(query, content[:2000], embedder)
                if score >= 0.3:
                    snippet = content[:200].strip()
                    hits.append((fp, 1, snippet, float(score)))
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
            "evidence_text": (hit.get("text", "") or
                              hit.get("snippet", ""))[:200],
            "confidence": 0.9,
            "claim_supported": query,
            "research_id": research_id,
        })
        memory.link(research_id, cit_id, "CITES")
    return {"citations": len(results),
            "summary": f"web: {len(results)} hits for {query!r}"}
