"""Spec 044 — research.verify: adversarial citation checks.

v1 ships two decidable checks (web-reachability deferred to v2):
  - evidence-supports-claim — substring match OR semantic ≥ 0.5
  - contradiction-cluster   — flag opposing claims with semantically
    distant evidence (≥ 0.7)
"""
import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def iid(engine):
    return engine.intent.capture_and_confirm(
        "test verifier", "x", "x", owner="user")


def _call(engine, iid, verb, **kw):
    r, _ = engine.registry.invoke(
        engine.memory, iid, "research", verb,
        agent_id="agent:test", **kw)
    return r


def _seed_research(engine, iid):
    r = _call(engine, iid, "lead", question="q", depth="brief")
    return r["research_id"]


def _add_citation(engine, rid, claim_text: str, evidence: str,
                  source_kind: str = "codebase",
                  confidence: float = 1.0,
                  url_or_path: str = "agency/x.py"):
    """Manually add a Citation + ResearchClaim node + edges."""
    claim_id = engine.memory.record("ResearchClaim", {"text": claim_text,
                                                       "research_id": rid})
    cit_id = engine.memory.record("Citation", {
        "source_kind": source_kind,
        "source_url_or_path": url_or_path,
        "evidence_text": evidence,
        "confidence": confidence,
        "claim_supported": claim_text,
        "research_id": rid,
    })
    engine.memory.link(rid, cit_id, "CITES")
    engine.memory.link(cit_id, claim_id, "SUPPORTS")
    return cit_id, claim_id


# ---------------------------------------------------------------------------
# evidence-supports-claim
# ---------------------------------------------------------------------------


def test_verify_passes_when_evidence_substring_matches(engine, iid):
    rid = _seed_research(engine, iid)
    _add_citation(engine, rid,
                  claim_text="dispatch picks driver via signals",
                  evidence="the dispatch function picks driver via signals")
    r = _call(engine, iid, "verify", research_id=rid)
    assert r["ok"]
    assert r["checks"]["evidence-supports-claim"]["status"] == "pass"


def test_verify_fails_when_evidence_unrelated(engine, iid):
    rid = _seed_research(engine, iid)
    _add_citation(engine, rid,
                  claim_text="dispatch picks driver via signals",
                  evidence="completely unrelated text about cats and dogs")
    r = _call(engine, iid, "verify", research_id=rid)
    assert not r["ok"]
    check = r["checks"]["evidence-supports-claim"]
    assert check["status"] == "fail"
    assert check.get("items")    # offending citations listed


# ---------------------------------------------------------------------------
# contradiction-cluster
# ---------------------------------------------------------------------------


def test_verify_flags_contradiction_cluster(engine, iid):
    rid = _seed_research(engine, iid)
    # Two claims that contradict each other.
    _add_citation(engine, rid,
                  claim_text="dispatch always picks local driver",
                  evidence="dispatch always picks local driver")
    _add_citation(engine, rid,
                  claim_text="dispatch never picks local driver",
                  evidence="dispatch never picks local driver")
    r = _call(engine, iid, "verify", research_id=rid)
    cc = r["checks"]["contradiction-cluster"]
    assert cc["status"] in ("warn", "fail")
    assert cc.get("items")


def test_verify_records_verification_node(engine, iid):
    rid = _seed_research(engine, iid)
    _add_citation(engine, rid,
                  claim_text="x", evidence="x")
    r = _call(engine, iid, "verify", research_id=rid)
    vs = engine.memory.find("Verification")
    ours = [v for v in vs if v.get("research_id") == rid]
    assert len(ours) == 1
    assert ours[0]["status"] in ("pass", "warn", "fail")


def test_verify_links_verifies_research(engine, iid):
    rid = _seed_research(engine, iid)
    _add_citation(engine, rid, claim_text="x", evidence="x")
    r = _call(engine, iid, "verify", research_id=rid)
    rows = engine.memory.g.query(
        "MATCH (v:Verification)-[:VERIFIES]->(r:Research) "
        "WHERE r.id = $rid RETURN v",
        {"rid": rid})
    assert len(rows) >= 1


def test_verify_empty_research_fails(engine, iid):
    """No citations → fail. Per PR #17 review: a Research that no
    specialist phase ever cited cannot be certified — the deep-research
    flow must refuse to publish a citation-free result. Replaces the
    earlier vacuous-pass shape from before the review fix."""
    rid = _seed_research(engine, iid)
    r = _call(engine, iid, "verify", research_id=rid)
    assert not r["ok"], (
        "empty Research must not pass verify; "
        f"got checks={r['checks']}")
    evidence_check = r["checks"]["evidence-supports-claim"]
    assert evidence_check["status"] == "fail"
    assert evidence_check["n_checked"] == 0
