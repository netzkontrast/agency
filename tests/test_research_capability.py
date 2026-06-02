"""Spec 044 — research capability: lead + specialist verbs.

Test plan:
  - lead mints a Research node, returns plan, depth-driven specialists
  - specialist (codebase) records Citation nodes with deterministic confidence
  - specialist (prior-reflections) reuses reflect.recall_semantic + score
  - specialist (doc-corpus) walks docs/ for keyword matches + score
  - ontology fragment registered (Research, Citation, ResearchClaim,
    Verification nodes; CITES, SUPPORTS, VERIFIES edges)
  - capability lints clean in block mode
"""
import os
import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def iid(engine):
    i = engine.intent.capture_and_confirm(
        "test research capability",
        "Research + Citation + Verification graph recorded",
        "verifier returns ok=True on coherent fixtures",
        owner="user")
    return i


def _call(engine, iid, verb, **kw):
    r, _ = engine.registry.invoke(
        engine.memory, iid, "research", verb,
        agent_id="agent:test", **kw)
    return r


# ---------------------------------------------------------------------------
# Capability + ontology registration.
# ---------------------------------------------------------------------------


def test_capability_registered(engine):
    assert "research" in engine.registry.names()


def test_capability_has_verbs(engine):
    verbs = set(engine.registry.get("research").verbs)
    assert {"lead", "specialist", "verify"} <= verbs


def test_ontology_research_status_enum(engine):
    enums = engine.ontology.enums
    assert ("Research", "status") in enums
    assert enums[("Research", "status")] == {
        "planning", "fanning-out", "verifying", "ready", "blocked", "published"}


def test_ontology_citation_source_kind_enum(engine):
    enums = engine.ontology.enums
    assert ("Citation", "source_kind") in enums
    assert enums[("Citation", "source_kind")] >= {
        "codebase", "reflection", "doc-corpus"}


def test_ontology_verification_status_enum(engine):
    enums = engine.ontology.enums
    assert enums[("Verification", "status")] == {"pass", "warn", "fail"}


def test_deep_research_skill_registered(engine):
    skills = engine.ontology.skills
    assert "deep-research" in skills
    phases = [p["name"] for p in skills["deep-research"]["phases"]]
    # Spec 044 walker: scope → plan → fan-out → verify → render → publish.
    # v1 ships with the 4-phase plan→fan-out→verify→publish core (render
    # scope on document.render is a v2 followup).
    assert "plan" in phases
    assert "verify" in phases
    assert "publish" in phases
    # The last phase is the hard publish gate.
    last = skills["deep-research"]["phases"][-1]
    assert last["name"] == "publish"
    assert last.get("gate") == "hard"


# ---------------------------------------------------------------------------
# research.lead — scope + plan fan-out.
# ---------------------------------------------------------------------------


def test_lead_brief_one_specialist(engine, iid):
    r = _call(engine, iid, "lead",
              question="how does dispatch_decision pick a driver?",
              depth="brief")
    assert "research_id" in r
    assert r["specialists"] == ["codebase"]   # brief defaults to codebase only
    assert r["plan"]   # non-empty


def test_lead_standard_two_specialists(engine, iid):
    r = _call(engine, iid, "lead",
              question="what is the dispatch heuristic",
              depth="standard")
    assert len(r["specialists"]) == 2
    assert "codebase" in r["specialists"]


def test_lead_deep_three_specialists(engine, iid):
    r = _call(engine, iid, "lead",
              question="how do agency capabilities compose",
              depth="deep")
    assert len(r["specialists"]) >= 3


def test_lead_records_research_node(engine, iid):
    r = _call(engine, iid, "lead",
              question="x", depth="brief")
    rid = r["research_id"]
    nodes = engine.memory.find("Research")
    assert any(n["id"] == rid for n in nodes)
    me = next(n for n in nodes if n["id"] == rid)
    assert me["question"] == "x"
    assert me["depth"] == "brief"
    assert me["status"] == "planning"


def test_lead_links_serves_intent(engine, iid):
    r = _call(engine, iid, "lead", question="x", depth="brief")
    rows = engine.memory.g.query(
        "MATCH (r:Research)-[:SERVES]->(i:Intent) "
        "WHERE r.id = $rid RETURN i",
        {"rid": r["research_id"]})
    assert len(rows) == 1
    assert rows[0]["i"]["properties"]["id"] == iid


# ---------------------------------------------------------------------------
# research.specialist — codebase + prior-reflections + doc-corpus.
# ---------------------------------------------------------------------------


def test_specialist_codebase_records_citations(engine, iid):
    plan = _call(engine, iid, "lead", question="dispatch", depth="brief")
    rid = plan["research_id"]
    # Codebase specialist with a query that matches something in agency/.
    r = _call(engine, iid, "specialist",
              research_id=rid, role="codebase",
              query="dispatch_decision",
              search_root="agency")
    assert r["citations"] >= 1
    assert r["summary"]


def test_codebase_citations_confidence_is_one(engine, iid):
    plan = _call(engine, iid, "lead", question="x", depth="brief")
    rid = plan["research_id"]
    _call(engine, iid, "specialist",
          research_id=rid, role="codebase",
          query="dispatch_decision",
          search_root="agency")
    citations = engine.memory.find("Citation")
    rs = [c for c in citations if c.get("research_id") == rid]
    # Codebase confidence is deterministic 1.0 (Spec 044 §"confidence
    # computation rule").
    assert rs
    assert all(c["confidence"] == 1.0 for c in rs)
    assert all(c["source_kind"] == "codebase" for c in rs)


def test_specialist_prior_reflections(engine, iid):
    # Seed a reflection so recall_semantic has something to find.
    engine.registry.invoke(engine.memory, iid, "reflect", "note",
                           agent_id="agent:test", scope="technical",
                           text="dispatch decision uses 11 signals")
    plan = _call(engine, iid, "lead", question="x", depth="brief")
    rid = plan["research_id"]
    r = _call(engine, iid, "specialist",
              research_id=rid, role="prior-reflections",
              query="dispatch signals")
    assert r["citations"] >= 1
    citations = engine.memory.find("Citation")
    rs = [c for c in citations if c.get("research_id") == rid]
    assert any(c["source_kind"] == "reflection" for c in rs)


def test_specialist_doc_corpus(engine, iid, tmp_path):
    # Build a small docs/ fixture.
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "test.md").write_text(
        "# test\n\nThis explains dispatch_decision heuristics.\n")
    plan = _call(engine, iid, "lead", question="x", depth="brief")
    rid = plan["research_id"]
    r = _call(engine, iid, "specialist",
              research_id=rid, role="doc-corpus",
              query="dispatch_decision",
              docs_root=str(docs))
    assert r["citations"] >= 1


def test_specialist_unknown_role_errors(engine, iid):
    plan = _call(engine, iid, "lead", question="x", depth="brief")
    rid = plan["research_id"]
    r = _call(engine, iid, "specialist",
              research_id=rid, role="not-a-role", query="x")
    assert "error" in r


# ---------------------------------------------------------------------------
# Engine kwarg + injector for web_search (Spec 044 §"Web-search boundary").
# ---------------------------------------------------------------------------


def test_engine_accepts_web_search_kwarg():
    """Engine wiring exposes the web_search injector even when v1 defaults
    web_search to None — keeps the boundary slot reserved."""
    class _StubWebSearch:
        name = "stub"
        def search(self, query, k=5):
            return [{"url": "https://x.test/1", "text": query, "title": "T"}]
    e = Engine(tempfile.mktemp(suffix=".db"), web_search=_StubWebSearch())
    assert e.web_search is not None
    assert e.web_search.name == "stub"
