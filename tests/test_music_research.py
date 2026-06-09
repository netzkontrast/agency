"""music research cluster — Spec 099 verb + skill coverage.

8 new verbs + 1 composite gate verb. All delegate to agency.research (Spec
044) — zero new drivers. Music adds AlbumClaim + AlbumVerification nodes
(music-scoped; agency.research has its own ResearchClaim/VerificationRecord
for the research-capability layer).

Spec 099 Done When line 68: `scripts/test-cap music_research` Green.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.capabilities.music.drivers import fake_drivers
from agency.engine import Engine
from agency.skill import SkillRun


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"), drivers=fake_drivers())


def _confirmed_iid(e: Engine, purpose: str = "research") -> str:
    iid = e.intent.capture(purpose, "deliverable", "acceptance")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "music", verb, **kw)


def test_research_cluster_verbs_discover() -> None:
    e = _fresh()
    verbs = e.registry._caps["music"].verbs
    for v in ("research_scope", "dispatch_research", "capture_claim",
              "verify_sources", "list_claims", "pending_verifications",
              "human_signoff", "document_hunt", "verify_gate"):
        assert v in verbs, f"verb {v!r} not registered"
    e.memory.close()


def test_research_workflow_skill_is_five_phased() -> None:
    e = _fresh()
    sk = e.ontology.skill("research-workflow")
    assert sk["kind"] == "workflow"
    assert len(sk["phases"]) == 5
    assert sk["phases"][-1].get("gate") == "hard"
    names = [p["name"] for p in sk["phases"]]
    assert names == ["scope", "dispatch-specialists", "collect",
                     "verify", "human-sign-off"]
    e.memory.close()


def test_album_claim_verified_enum_bites() -> None:
    """(AlbumClaim, verified) enum {pending, human-confirmed, rejected}."""
    e = _fresh()
    with pytest.raises(ValueError):
        e.memory.record("AlbumClaim", {
            "text": "x", "source_uri": "http://a", "domain": "legal",
            "verified": "nonsense"})
    e.memory.close()


def test_album_claim_domain_enum_bites() -> None:
    e = _fresh()
    with pytest.raises(ValueError):
        e.memory.record("AlbumClaim", {
            "text": "x", "source_uri": "http://a",
            "domain": "not_a_domain", "verified": "pending"})
    e.memory.close()


def test_capture_claim_records_node_and_serves_intent() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "capture_claim",
                        text="The defendant pled guilty",
                        source_uri="https://courtlistener.com/x",
                        domain="legal", album="case-files")
    assert data["claim_id"].startswith("albumclaim:")
    assert data["domain"] == "legal"
    assert data["verified"] == "pending"
    # SERVES edge present
    rows = e.memory.g.query(
        "MATCH (c)-[r:SERVES]->(i) WHERE c.id = $cid AND i.id = $iid RETURN r",
        {"cid": data["claim_id"], "iid": iid})
    assert rows
    e.memory.close()


def test_capture_claim_rejects_unknown_domain() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "capture_claim",
                        text="x", source_uri="http://a",
                        domain="polka", album="A")
    assert data is None
    assert "INVALID_ARGUMENT" in e.memory.recall(inv).get("error", "")
    e.memory.close()


def test_list_claims_filters_by_status() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "capture_claim", text="c1",
            source_uri="http://a", domain="legal", album="A")
    _invoke(e, iid, "capture_claim", text="c2",
            source_uri="http://b", domain="financial", album="A")
    all_, _ = _invoke(e, iid, "list_claims")
    pending, _ = _invoke(e, iid, "list_claims", status="pending")
    confirmed, _ = _invoke(e, iid, "list_claims", status="human-confirmed")
    assert all_["count"] == 2
    assert pending["count"] == 2
    assert confirmed["count"] == 0
    e.memory.close()


def test_pending_verifications_aggregates_by_domain() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "capture_claim", text="c1",
            source_uri="http://a", domain="legal", album="A")
    _invoke(e, iid, "capture_claim", text="c2",
            source_uri="http://b", domain="legal", album="A")
    _invoke(e, iid, "capture_claim", text="c3",
            source_uri="http://c", domain="financial", album="A")
    data, _ = _invoke(e, iid, "pending_verifications", album="A")
    assert data["pending_count"] == 3
    assert data["by_domain"]["legal"] == 2
    assert data["by_domain"]["financial"] == 1
    e.memory.close()


def test_verify_sources_clears_pending_claims() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    for d in ("legal", "financial", "primary_source"):
        _invoke(e, iid, "capture_claim",
                text=f"claim {d}", source_uri="http://a",
                domain=d, album="A")
    data, _ = _invoke(e, iid, "verify_sources", album="A")
    assert data["verified_count"] == 3
    # All claims now human-confirmed
    after, _ = _invoke(e, iid, "list_claims", status="pending")
    assert after["count"] == 0
    e.memory.close()


def test_verify_gate_passes_when_no_pending() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    data, _ = _invoke(e, iid, "verify_gate", lifecycle_id=lc, album="A")
    assert data["passed"] is True
    assert data["pending_count"] == 0
    e.memory.close()


def test_verify_gate_blocks_when_pending_exists() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "capture_claim", text="pending",
            source_uri="http://a", domain="legal", album="A")
    lc = e.lifecycle.open(iid)
    data, inv = _invoke(e, iid, "verify_gate", lifecycle_id=lc, album="A")
    assert data is None
    assert "GATE_FAILED" in e.memory.recall(inv).get("error", "")
    assert "1 pending" in e.memory.recall(inv).get("error", "")
    assert e.memory.recall(lc).get("state") == "input-required"
    e.memory.close()


def test_human_signoff_records_verification_record() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "human_signoff", album="Origin",
                      reviewer="alice")
    assert data["album"] == "Origin"
    assert data["reviewer"] == "alice"
    assert data["signoff_id"].startswith("albumverification:")
    e.memory.close()


def test_document_hunt_delegates_to_research_lead() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "document_hunt",
                      query="SEC enforcement actions 2023")
    assert "research_id" in data
    assert data["domain"] == "document_hunter"
    assert "query" in data
    e.memory.close()


def test_research_scope_delegates_to_research_lead() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "research_scope",
                      question="What happened in 2008?",
                      album="A", depth="deep")
    assert "research_id" in data
    assert "specialists" in data
    assert data["album"] == "A"
    e.memory.close()


def test_dispatch_research_handles_all_domains_default() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    scope, _ = _invoke(e, iid, "research_scope",
                       question="x", album="A")
    rid = scope["research_id"]
    data, _ = _invoke(e, iid, "dispatch_research", research_id=rid,
                      album="A")
    # Default = all 10 domains
    assert data["count"] == 10
    assert "legal" in data["dispatched_to"]
    e.memory.close()


def test_research_workflow_skill_walks_through_signoff() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    sk = e.ontology.skill("research-workflow")
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"research_question": "Q", "domains_selected": "legal,financial"},
        {"specialists_dispatched": "yes"},
        {"claims_captured": "3"},
        {"pending_resolved": "yes"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"sources_signed_off": "yes"},
                      confirmed=True)["status"] == "completed"
    e.memory.close()
