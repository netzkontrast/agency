"""Spec 045 — semantic recall over Reflection nodes.

Covers the verb (`reflect.recall_semantic`), the embedder boundary
(`_embed.py`), the engine injector slot (`embedder=`), and the
`agency_doctor` payload field.
"""
import tempfile

import pytest

from agency.engine import Engine


# ---------------------------------------------------------------------------
# Fixture corpora.
# ---------------------------------------------------------------------------


def _seed(engine, iid, items: list[tuple[str, str]]) -> list[str]:
    """Write (scope, text) reflections; return their ids."""
    ids = []
    for scope, text in items:
        r, _ = engine.registry.invoke(
            engine.memory, iid, "reflect", "note",
            agent_id="agent:test", scope=scope, text=text)
        ids.append(r["result"])
    return ids


def _iid(engine):
    intent = engine.intent.capture(
        "test semantic recall",
        "results sorted by relevance",
        "stub embedder used when injected",
    )
    engine.intent.confirm(intent)
    return intent


# ---------------------------------------------------------------------------
# Verb signature + payload shape.
# ---------------------------------------------------------------------------


def test_recall_semantic_returns_documented_payload():
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = _iid(e)
    _seed(e, iid, [
        ("technical", "fix MCP startup hang on Linux"),
        ("technical", "solved the FastMCP bind issue with a port retry"),
        ("project", "shipping v0.2 next week"),
    ])
    r, _ = e.registry.invoke(
        e.memory, iid, "reflect", "recall_semantic",
        agent_id="agent:test", query="fix MCP startup", k=3)
    # Top-level shape.
    assert "results" in r
    assert "embedder" in r
    assert r["embedder"] == "tfidf"
    # Per-result shape (Spec 045 line 57–60).
    for hit in r["results"]:
        for key in ("id", "score", "scope", "text", "vfrom"):
            assert key in hit, f"missing {key} in result"
        assert isinstance(hit["score"], float)
        assert 0.0 <= hit["score"] <= 1.0


def test_results_sorted_by_score_desc():
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = _iid(e)
    _seed(e, iid, [
        ("technical", "fix MCP startup hang on Linux"),
        ("technical", "solved the FastMCP bind issue with a port retry"),
        ("project", "shipping v0.2 next week"),
        ("world", "great pizza in Berlin"),
    ])
    r, _ = e.registry.invoke(
        e.memory, iid, "reflect", "recall_semantic",
        agent_id="agent:test", query="MCP startup fix")
    scores = [h["score"] for h in r["results"]]
    assert scores == sorted(scores, reverse=True)


def test_k_param_limits_results():
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = _iid(e)
    _seed(e, iid, [
        ("technical", f"reflection #{i} about MCP") for i in range(10)
    ])
    r, _ = e.registry.invoke(
        e.memory, iid, "reflect", "recall_semantic",
        agent_id="agent:test", query="MCP", k=3)
    assert len(r["results"]) <= 3


def test_text_truncated_to_200_chars():
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = _iid(e)
    long_text = "MCP " + "x" * 500
    _seed(e, iid, [("technical", long_text)])
    r, _ = e.registry.invoke(
        e.memory, iid, "reflect", "recall_semantic",
        agent_id="agent:test", query="MCP")
    assert all(len(h["text"]) <= 200 for h in r["results"])


# ---------------------------------------------------------------------------
# TF-IDF default backend: sensible ranking on paraphrases.
# ---------------------------------------------------------------------------


def test_tfidf_finds_paraphrase_via_shared_terms():
    """Spec 045 §"Done When" line 100–102: 'fix MCP startup' should match
    'I solved the FastMCP bind issue' — both share MCP-domain terms."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = _iid(e)
    _seed(e, iid, [
        ("technical", "I solved the FastMCP bind issue with a port retry"),
        ("world", "the weather is great today"),
        ("project", "shipping v0.2 next week"),
    ])
    r, _ = e.registry.invoke(
        e.memory, iid, "reflect", "recall_semantic",
        agent_id="agent:test", query="fix FastMCP startup")
    # Top result is the technical paraphrase, not the world/project rows.
    top = r["results"][0]
    assert "FastMCP" in top["text"]
    assert top["scope"] == "technical"


def test_empty_corpus_returns_empty_results():
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = _iid(e)
    r, _ = e.registry.invoke(
        e.memory, iid, "reflect", "recall_semantic",
        agent_id="agent:test", query="anything")
    assert r == {"results": [], "embedder": "tfidf"}


def test_empty_query_returns_empty_results():
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = _iid(e)
    _seed(e, iid, [("technical", "some content")])
    r, _ = e.registry.invoke(
        e.memory, iid, "reflect", "recall_semantic",
        agent_id="agent:test", query="")
    assert r["results"] == []


# ---------------------------------------------------------------------------
# Scope filter applies AFTER ranking (Spec 045 line 104–106).
# ---------------------------------------------------------------------------


def test_scope_filter_post_ranking():
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = _iid(e)
    _seed(e, iid, [
        ("world",     "great pizza place near MCP street"),
        ("technical", "fix MCP startup hang via port retry"),
        ("world",     "MCP convention in Berlin next year"),
    ])
    r, _ = e.registry.invoke(
        e.memory, iid, "reflect", "recall_semantic",
        agent_id="agent:test", query="MCP startup", scope="technical")
    # Only technical reflections returned.
    assert all(h["scope"] == "technical" for h in r["results"])
    assert len(r["results"]) >= 1


# ---------------------------------------------------------------------------
# Embedder boundary: injected stub is honoured.
# ---------------------------------------------------------------------------


class _StubEmbedder:
    """Test stub: returns descending scores by row index — proves the
    boundary is wired (no real similarity computation)."""
    name = "stub"

    def index(self, corpus):
        return corpus    # opaque to scoring; just hand it back

    def score(self, query, indexed):
        n = len(indexed)
        # First row scores 1.0, last scores ~0.0; deterministic.
        return [1.0 - (i / max(n, 1)) for i in range(n)]


def test_injected_embedder_is_used():
    stub = _StubEmbedder()
    e = Engine(tempfile.mktemp(suffix=".db"), embedder=stub)
    iid = _iid(e)
    _seed(e, iid, [
        ("technical", "alpha"),
        ("technical", "beta"),
        ("technical", "gamma"),
    ])
    r, _ = e.registry.invoke(
        e.memory, iid, "reflect", "recall_semantic",
        agent_id="agent:test", query="anything")
    assert r["embedder"] == "stub"
    # Stub assigns descending scores in insertion order; result order
    # follows. With 3 rows we expect "alpha" first (score 1.0),
    # then "beta", then "gamma".
    assert r["results"][0]["text"] == "alpha"


# ---------------------------------------------------------------------------
# Engine wiring + agency_doctor surfacing.
# ---------------------------------------------------------------------------


def test_engine_resolves_default_embedder_when_none_passed():
    e = Engine(tempfile.mktemp(suffix=".db"))
    assert getattr(e, "embedder", None) is not None
    assert e.embedder.name == "tfidf"


def test_engine_honours_kwarg_embedder():
    stub = _StubEmbedder()
    e = Engine(tempfile.mktemp(suffix=".db"), embedder=stub)
    assert e.embedder is stub


def test_agency_doctor_reports_embedder_name():
    """agency_doctor is a substrate MCP tool — reach it via the FastMCP
    client like tests/test_agency_doctor.py does."""
    import asyncio
    import json
    from fastmcp import Client

    def _sc(result):
        sc = result.structured_content
        if isinstance(sc, dict):
            return sc.get("result", sc)
        if sc is not None:
            return sc
        if result.content:
            try:
                return json.loads(result.content[0].text)
            except (ValueError, TypeError):
                return result.content[0].text
        return None

    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_doctor", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    assert "embedder" in out
    assert out["embedder"] == "tfidf"


# ---------------------------------------------------------------------------
# No regression to existing recall/search.
# ---------------------------------------------------------------------------


def test_recall_still_works():
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = _iid(e)
    _seed(e, iid, [("technical", "still works")])
    r, _ = e.registry.invoke(
        e.memory, iid, "reflect", "recall",
        agent_id="agent:test")
    assert r["result"][0]["text"] == "still works"


def test_search_still_works():
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = _iid(e)
    _seed(e, iid, [("technical", "MCP startup fix")])
    r, _ = e.registry.invoke(
        e.memory, iid, "reflect", "search",
        agent_id="agent:test", query="startup")
    assert len(r["result"]) == 1


# ---------------------------------------------------------------------------
# Embedder resolver behavior (importable for engine wiring).
# ---------------------------------------------------------------------------


def test_resolve_embedder_defaults_to_tfidf(monkeypatch):
    from agency.capabilities._embed import resolve_embedder
    monkeypatch.delenv("AGENCY_EMBEDDER", raising=False)
    emb = resolve_embedder()
    assert emb.name == "tfidf"


def test_resolve_embedder_unknown_target_falls_back(monkeypatch):
    from agency.capabilities._embed import resolve_embedder
    monkeypatch.setenv("AGENCY_EMBEDDER", "no-such-backend-xyz")
    emb = resolve_embedder()
    # Falls back silently — agency_doctor would surface the fallback.
    assert emb.name == "tfidf"


def test_k_zero_returns_empty_results():
    """Edge case from code review (F13): k <= 0 must short-circuit to
    empty results, not slice a list with negative k (which would return
    all-but-last-k)."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = _iid(e)
    _seed(e, iid, [("technical", "MCP startup fix")])
    r, _ = e.registry.invoke(
        e.memory, iid, "reflect", "recall_semantic",
        agent_id="agent:test", query="MCP", k=0)
    assert r["results"] == []
    # Negative k must also short-circuit (Python's [:negative] would
    # otherwise return rows minus the last |k|).
    r, _ = e.registry.invoke(
        e.memory, iid, "reflect", "recall_semantic",
        agent_id="agent:test", query="MCP", k=-2)
    assert r["results"] == []


def test_agency_doctor_surfaces_bge_fallback(monkeypatch):
    """Code-review F9: when AGENCY_EMBEDDER requests a backend that
    resolved to TF-IDF (e.g. BGE without [recall] extra), agency_doctor
    must surface the fallback in next_steps so users see the gap."""
    import asyncio
    import json
    from fastmcp import Client

    def _sc(result):
        sc = result.structured_content
        if isinstance(sc, dict):
            return sc.get("result", sc)
        if sc is not None:
            return sc
        if result.content:
            try:
                return json.loads(result.content[0].text)
            except (ValueError, TypeError):
                return result.content[0].text
        return None

    monkeypatch.setenv("AGENCY_EMBEDDER", "bge-small-en")
    e = Engine(tempfile.mktemp(suffix=".db"))
    # If sentence-transformers is actually installed in this env, this
    # test makes no claim — the request succeeded.
    if e.embedder.name == "bge-small-en":
        pytest.skip("BGE is installed; the fallback path isn't triggered")
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_doctor", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    assert out["embedder"] == "tfidf"
    # Surface the fallback as a copy-pasteable next step.
    assert any("AGENCY_EMBEDDER" in s and "recall" in s for s in out["next_steps"])


def test_agency_doctor_surfaces_unknown_backend_typo(monkeypatch):
    """Code-review F9 follow-up: when AGENCY_EMBEDDER names a backend
    that isn't known, agency_doctor names the valid options — `pip
    install` won't help for a typo."""
    import asyncio
    import json
    from fastmcp import Client

    def _sc(result):
        sc = result.structured_content
        if isinstance(sc, dict):
            return sc.get("result", sc)
        if sc is not None:
            return sc
        if result.content:
            try:
                return json.loads(result.content[0].text)
            except (ValueError, TypeError):
                return result.content[0].text
        return None

    monkeypatch.setenv("AGENCY_EMBEDDER", "tf-idf")  # typo'd; should be "tfidf"
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_doctor", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    assert out["embedder"] == "tfidf"
    # The next-step mentions the typo'd name AND lists valid options.
    assert any("'tf-idf'" in s and "tfidf" in s and "bge-small-en" in s
               for s in out["next_steps"])
