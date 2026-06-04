"""Spec 052 — research web specialist + reachability verifier check.

Closes Spec 044 v1 scope-cut (web specialist returned 'no driver' when
web_search=None). v1 ships:
  - DuckDuckGoClient — zero-config default WebSearchClient using
    DuckDuckGo Instant Answer API (no key, JSON)
  - resolve_web_search() — env-driven resolution (AGENCY_WEB_BACKEND);
    matches Spec 045 resolve_embedder pattern
  - Engine wires resolve_web_search() as default
  - research.verify gains a third check: web-reachability (HEAD URLs)
"""
import json
import tempfile
from unittest import mock

import pytest

from agency.engine import Engine


# ---------------------------------------------------------------------------
# DuckDuckGoClient — search returns parsed list[{url, title, text}]
# ---------------------------------------------------------------------------


def _mock_response(json_payload, status_code=200):
    m = mock.MagicMock()
    m.status_code = status_code
    m.json.return_value = json_payload
    m.raise_for_status.return_value = None
    return m


def test_ddg_client_parses_related_topics():
    from agency.capabilities.research._web import DuckDuckGoClient
    client = DuckDuckGoClient()
    assert client.name == "duckduckgo"
    fake = {
        "AbstractText": "Python is a programming language.",
        "AbstractURL": "https://en.wikipedia.org/wiki/Python",
        "Heading": "Python",
        "RelatedTopics": [
            {"FirstURL": "https://example.com/topic1",
              "Text": "Topic 1 about Python"},
            {"FirstURL": "https://example.com/topic2",
              "Text": "Topic 2 about Python"},
        ],
    }
    with mock.patch("httpx.Client") as MockClient:
        instance = MockClient.return_value.__enter__.return_value
        instance.get.return_value = _mock_response(fake)
        results = client.search("Python language", k=5)
    assert results
    # AbstractText becomes the first hit; RelatedTopics fill the rest.
    assert results[0]["url"] == "https://en.wikipedia.org/wiki/Python"
    assert "Python" in results[0]["text"]
    urls = {r["url"] for r in results}
    assert "https://example.com/topic1" in urls


def test_ddg_client_returns_empty_on_failure():
    from agency.capabilities.research._web import DuckDuckGoClient
    client = DuckDuckGoClient()
    with mock.patch("httpx.Client") as MockClient:
        instance = MockClient.return_value.__enter__.return_value
        instance.get.side_effect = Exception("network down")
        results = client.search("query", k=5)
    assert results == []


def test_ddg_client_respects_k_limit():
    from agency.capabilities.research._web import DuckDuckGoClient
    fake = {
        "AbstractText": "x",
        "AbstractURL": "https://x.test/abstract",
        "RelatedTopics": [
            {"FirstURL": f"https://t.test/{i}", "Text": f"t{i}"}
            for i in range(10)
        ],
    }
    client = DuckDuckGoClient()
    with mock.patch("httpx.Client") as MockClient:
        instance = MockClient.return_value.__enter__.return_value
        instance.get.return_value = _mock_response(fake)
        results = client.search("x", k=3)
    assert len(results) <= 3


# ---------------------------------------------------------------------------
# resolve_web_search — env > unknown-fallback > default
# ---------------------------------------------------------------------------


def test_resolve_defaults_to_duckduckgo(monkeypatch):
    from agency.capabilities.research._web import resolve_web_search
    monkeypatch.delenv("AGENCY_WEB_BACKEND", raising=False)
    backend = resolve_web_search()
    assert backend.name == "duckduckgo"


def test_resolve_explicit_duckduckgo(monkeypatch):
    from agency.capabilities.research._web import resolve_web_search
    monkeypatch.setenv("AGENCY_WEB_BACKEND", "duckduckgo")
    backend = resolve_web_search()
    assert backend.name == "duckduckgo"


def test_resolve_unknown_falls_back_silently(monkeypatch):
    """Unknown backend → DuckDuckGo (matches Spec 045 embedder fallback)."""
    from agency.capabilities.research._web import resolve_web_search
    monkeypatch.setenv("AGENCY_WEB_BACKEND", "no-such-backend")
    backend = resolve_web_search()
    assert backend.name == "duckduckgo"


def test_engine_default_web_search_is_duckduckgo(monkeypatch):
    """Engine wires resolve_web_search() as the default."""
    monkeypatch.delenv("AGENCY_WEB_BACKEND", raising=False)
    e = Engine(tempfile.mktemp(suffix=".db"))
    assert e.web_search is not None
    assert e.web_search.name == "duckduckgo"


def test_engine_kwarg_overrides_default():
    class StubClient:
        name = "stub"
        def search(self, q, k=5): return []
    e = Engine(tempfile.mktemp(suffix=".db"), web_search=StubClient())
    assert e.web_search.name == "stub"


# ---------------------------------------------------------------------------
# Web-reachability check in research.verify
# ---------------------------------------------------------------------------


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def iid(engine):
    return engine.intent.capture_and_confirm(
        "test web verify", "x", "x", owner="user")


def _call_research(engine, iid, verb, **kw):
    r, _ = engine.registry.invoke(
        engine.memory, iid, "research", verb,
        agent_id="agent:test", **kw)
    return r


def _add_web_citation(engine, rid, url, claim="x"):
    cit_id = engine.memory.record("Citation", {
        "source_kind": "web",
        "source_url_or_path": url,
        "evidence_text": "evidence text",
        "confidence": 0.9,
        "claim_supported": claim,
        "research_id": rid,
    })
    engine.memory.link(rid, cit_id, "CITES")
    return cit_id


def test_reachability_check_passes_on_2xx(engine, iid):
    """When all web URLs HEAD-succeed (2xx), reachability check passes."""
    r = _call_research(engine, iid, "lead", question="q", depth="brief")
    rid = r["research_id"]
    _add_web_citation(engine, rid, "https://reachable.test/1")
    with mock.patch("httpx.Client") as MockClient:
        instance = MockClient.return_value.__enter__.return_value
        resp = mock.MagicMock(status_code=200)
        instance.head.return_value = resp
        v = _call_research(engine, iid, "verify", research_id=rid)
    assert "web-reachability" in v["checks"]
    assert v["checks"]["web-reachability"]["status"] == "pass"


def test_reachability_check_fails_on_4xx(engine, iid):
    r = _call_research(engine, iid, "lead", question="q", depth="brief")
    rid = r["research_id"]
    _add_web_citation(engine, rid, "https://broken.test/404")
    with mock.patch("httpx.Client") as MockClient:
        instance = MockClient.return_value.__enter__.return_value
        instance.head.return_value = mock.MagicMock(status_code=404)
        v = _call_research(engine, iid, "verify", research_id=rid)
    check = v["checks"]["web-reachability"]
    assert check["status"] == "fail"
    assert check.get("items")


def test_reachability_check_fails_on_network_error(engine, iid):
    r = _call_research(engine, iid, "lead", question="q", depth="brief")
    rid = r["research_id"]
    _add_web_citation(engine, rid, "https://gone.test/")
    with mock.patch("httpx.Client") as MockClient:
        instance = MockClient.return_value.__enter__.return_value
        instance.head.side_effect = Exception("connect timeout")
        v = _call_research(engine, iid, "verify", research_id=rid)
    assert v["checks"]["web-reachability"]["status"] == "fail"


def test_reachability_check_vacuous_pass_when_no_web_citations(engine, iid):
    """Citations of kind != 'web' don't get reachability-checked; if
    no web citations exist, the check passes vacuously."""
    r = _call_research(engine, iid, "lead", question="q", depth="brief")
    rid = r["research_id"]
    # No web citations — only one codebase citation.
    cit = engine.memory.record("Citation", {
        "source_kind": "codebase",
        "source_url_or_path": "agency/x.py:1",
        "evidence_text": "x", "confidence": 1.0,
        "claim_supported": "x", "research_id": rid,
    })
    engine.memory.link(rid, cit, "CITES")
    v = _call_research(engine, iid, "verify", research_id=rid)
    assert v["checks"]["web-reachability"]["status"] == "pass"


def test_verify_payload_has_three_checks(engine, iid):
    r = _call_research(engine, iid, "lead", question="q", depth="brief")
    rid = r["research_id"]
    v = _call_research(engine, iid, "verify", research_id=rid)
    assert set(v["checks"]) == {
        "evidence-supports-claim",
        "contradiction-cluster",
        "web-reachability",
    }
