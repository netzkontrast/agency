"""Spec 105 Slice 1 — novel research cluster (graph-only verbs).

Mirrors music's 099 pattern (AlbumClaim → NovelClaim). Slice 1 ships
the 3 graph-only verbs that don't need agency.research delegation:
- capture_claim (effect) — records a NovelClaim
- list_claims (transform) — filter by status
- pending_verifications (transform) — count unverified

The delegating verbs (research_scope / dispatch_research / verify_sources
/ document_hunt) + composite verify_gate + research-workflow walkable
skill follow in Slice 2 once the wiring against agency.research is
exercised on a research-bearing novel intent.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "spec 105") -> str:
    iid = e.intent.capture(purpose, "research", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "novel", verb, **kw)


# ─────────────────────── registration ───────────────────────


def test_novel_capability_registers_research_verbs() -> None:
    e = _fresh()
    cap = e.registry._caps["novel"]
    expected = {"capture_claim", "list_claims", "pending_verifications"}
    missing = expected - set(cap.verbs)
    assert not missing, f"missing research verbs: {missing}"
    e.memory.close()


def test_novel_claim_node_declared() -> None:
    e = _fresh()
    cap = e.registry._caps["novel"]
    assert "NovelClaim" in cap.ontology.nodes
    assert ("NovelClaim", "verified") in cap.ontology.enums
    e.memory.close()


def test_novel_claim_status_enum_bites() -> None:
    e = _fresh()
    with pytest.raises(ValueError):
        e.memory.record("NovelClaim",
                          {"text": "x", "source_uri": "u",
                           "domain": "historical",
                           "verified": "nonsense"})
    e.memory.close()


# ─────────────────────── capture_claim ───────────────────────


def test_capture_claim_records_node_serves_intent() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "capture_claim",
                      text="In 1984 BBS culture peaked at 60K nodes",
                      source_uri="https://archive.org/details/x",
                      domain="historical")
    assert data["claim_id"].startswith("novelclaim:")
    assert data["text"].startswith("In 1984")
    assert data["domain"] == "historical"
    assert data["verified"] == "pending"
    rows = e.memory.g.query(
        "MATCH (c)-[r:SERVES]->(t) WHERE c.id = $cid AND t.id = $tid RETURN r",
        {"cid": data["claim_id"], "tid": iid})
    assert rows
    e.memory.close()


def test_capture_claim_rejects_invalid_domain() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "capture_claim",
                        text="x", source_uri="u",
                        domain="not-a-domain")
    assert data is None
    err = e.memory.recall(inv).get("error", "")
    assert "INVALID_ARGUMENT" in err
    e.memory.close()


# ─────────────────────── list_claims ───────────────────────


def test_list_claims_filters_by_verified_status() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "capture_claim", text="a", source_uri="u1",
            domain="historical")
    _invoke(e, iid, "capture_claim", text="b", source_uri="u2",
            domain="scientific")
    _invoke(e, iid, "capture_claim", text="c", source_uri="u3",
            domain="cultural")
    all_, _ = _invoke(e, iid, "list_claims")
    assert all_["count"] == 3
    pending, _ = _invoke(e, iid, "list_claims", verified="pending")
    assert pending["count"] == 3
    confirmed, _ = _invoke(e, iid, "list_claims", verified="confirmed")
    assert confirmed["count"] == 0
    e.memory.close()


def test_list_claims_rejects_invalid_verified() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "list_claims", verified="bogus")
    assert data is None
    err = e.memory.recall(inv).get("error", "")
    assert "INVALID_ARGUMENT" in err
    e.memory.close()


# ─────────────────────── pending_verifications ───────────────────────


def test_pending_verifications_aggregates_pending() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "capture_claim", text="p1", source_uri="u",
            domain="historical")
    _invoke(e, iid, "capture_claim", text="p2", source_uri="u",
            domain="scientific")
    data, _ = _invoke(e, iid, "pending_verifications")
    assert data["count"] == 2
    assert data["by_domain"]["historical"] == 1
    assert data["by_domain"]["scientific"] == 1
    e.memory.close()
