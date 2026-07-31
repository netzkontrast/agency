"""Spec 247 — canon locks: approval workflow + dogfood pipe.

propose -> approve is the reviewed path to a Lock: the status DAG is legal-
transitions-only and approval is monotonic (idempotent repeat approve,
supersession via a NEW proposal); every approval-path Lock carries
proposed_by + approved_by + proposal_id and count(such Locks) ==
count(approved proposals); the K-tier evidence gate runs at propose-time;
rejection records a Reflection and scope churn (>= 3 rejections) mints one
observation Reflection; managed agents may propose, never approve.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 247", "canon approval", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e, iid, verb, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb, **kw)
    return r


def _novel(e, iid):
    return _invoke(e, iid, "create_novel", title="KP",
                   author="A")["novel_id"]


_PAYLOAD = {"rule": "no-resurrection", "scope_note": "magic-system"}


def test_full_propose_approve_flow_with_provenance() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    prop = _invoke(e, iid, "propose_canon", novel_id=nid,
                   scope="magic-system", payload=_PAYLOAD,
                   rationale="3x recurrence", proposed_by="mira")
    assert prop["status"] == "proposal"
    assert prop["intent_id"]                       # Spec 176 sub-intent
    dec = _invoke(e, iid, "approve_canon", proposal_id=prop["proposal_id"],
                  approver="lead-author")
    assert dec["decision"] == "approve" and dec["lock_id"]
    lock = e.memory.recall(dec["lock_id"])
    assert lock["proposed_by"] == "mira"
    assert lock["approved_by"] == "lead-author"
    assert lock["proposal_id"] == prop["proposal_id"]
    # the lock is live in the Master-Index
    idx = _invoke(e, iid, "lock_index", novel_id=nid)
    assert any(l["id"] == dec["lock_id"] for l in idx["locks"])
    # provenance relation: approval-path locks == approved proposals
    approved = _invoke(e, iid, "list_canon_proposals", novel_id=nid,
                       status="approved")["count"]
    prov_locks = [l for l in e.memory.find("Lock")
                  if l.get("proposal_id")]
    assert len(prov_locks) == approved
    e.memory.close()


def test_approval_is_monotonic_and_idempotent() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    pid = _invoke(e, iid, "propose_canon", novel_id=nid, scope="s",
                  payload=_PAYLOAD, rationale="r")["proposal_id"]
    first = _invoke(e, iid, "approve_canon", proposal_id=pid,
                    approver="anna")
    again = _invoke(e, iid, "approve_canon", proposal_id=pid,
                    approver="bert")
    assert again["idempotent"] is True             # first approval wins
    assert again["lock_id"] == first["lock_id"]
    assert again["decided_by"] == "anna"
    # approved cannot revert to rejected
    assert _invoke(e, iid, "approve_canon", proposal_id=pid,
                   approver="anna", decision="reject",
                   reason="changed my mind") is None
    e.memory.close()


def test_supersession_mints_new_proposal_and_keeps_lineage() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    p1 = _invoke(e, iid, "propose_canon", novel_id=nid, scope="veil",
                 payload=_PAYLOAD, rationale="v1")["proposal_id"]
    lock1 = _invoke(e, iid, "approve_canon", proposal_id=p1,
                    approver="anna")["lock_id"]
    p2 = _invoke(e, iid, "propose_canon", novel_id=nid, scope="veil",
                 payload={"rule": "v2"}, rationale="tighten",
                 supersedes_lock=lock1)["proposal_id"]
    lock2 = _invoke(e, iid, "approve_canon", proposal_id=p2,
                    approver="anna")["lock_id"]
    # old lock superseded (chain kept), old proposal flips to superseded
    assert e.memory.recall(lock1)["superseded_by"] == lock2
    assert e.memory.recall(p1)["status"] == "superseded"
    assert e.memory.recall(lock2)["supersedes"] == lock1
    # only the new lock is active
    idx = _invoke(e, iid, "lock_index", novel_id=nid, topic="veil")
    assert [l["id"] for l in idx["locks"]] == [lock2]
    e.memory.close()


def test_k_tier_evidence_gate_at_propose_time() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    # no evidence → typed failure
    assert _invoke(e, iid, "propose_canon", novel_id=nid, scope="s",
                   payload=_PAYLOAD, rationale="r", tier="K") is None
    # bogus evidence id → typed failure
    assert _invoke(e, iid, "propose_canon", novel_id=nid, scope="s",
                   payload=_PAYLOAD, rationale="r", tier="K",
                   evidence="lock:nope") is None
    # a real approved lock as evidence → accepted
    p0 = _invoke(e, iid, "propose_canon", novel_id=nid, scope="base",
                 payload=_PAYLOAD, rationale="V first")["proposal_id"]
    lock = _invoke(e, iid, "approve_canon", proposal_id=p0,
                   approver="anna")["lock_id"]
    ok = _invoke(e, iid, "propose_canon", novel_id=nid, scope="s",
                 payload=_PAYLOAD, rationale="promote", tier="K",
                 evidence=lock)
    assert ok["status"] == "proposal"
    # tier=author needs the explicit override
    assert _invoke(e, iid, "propose_canon", novel_id=nid, scope="s2",
                   payload=_PAYLOAD, rationale="r",
                   tier="author") is None
    assert _invoke(e, iid, "propose_canon", novel_id=nid, scope="s2",
                   payload=_PAYLOAD, rationale="r", tier="author",
                   author_override=True)["status"] == "proposal"
    # malformed payload rejected without minting anything
    assert _invoke(e, iid, "propose_canon", novel_id=nid, scope="s3",
                   payload={}, rationale="r") is None
    e.memory.close()


def test_rejection_records_reflection_and_churn_signal() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    churn_ids = []
    for i in range(3):
        pid = _invoke(e, iid, "propose_canon", novel_id=nid,
                      scope="noisy-rule", payload=_PAYLOAD,
                      rationale=f"try {i}")["proposal_id"]
        dec = _invoke(e, iid, "approve_canon", proposal_id=pid,
                      approver="anna", decision="reject",
                      reason="still too broad")
        assert dec["dogfood_reflection_id"]        # every rejection
        churn_ids.append(dec.get("churn_reflection_id", ""))
    assert churn_ids[0] == "" and churn_ids[1] == ""
    assert churn_ids[2]                            # 3rd rejection = churn
    churn = [r for r in e.memory.find("Reflection")
             if r.get("kind") == "canon-churn"
             and r.get("cluster") == "noisy-rule"]
    assert len(churn) == 1
    # a 4th rejection never re-mints the cluster
    pid = _invoke(e, iid, "propose_canon", novel_id=nid, scope="noisy-rule",
                  payload=_PAYLOAD, rationale="try 4")["proposal_id"]
    _invoke(e, iid, "approve_canon", proposal_id=pid, approver="anna",
            decision="reject", reason="nope")
    churn2 = [r for r in e.memory.find("Reflection")
              if r.get("kind") == "canon-churn"
              and r.get("cluster") == "noisy-rule"]
    assert len(churn2) == 1
    e.memory.close()


def test_managed_agent_may_propose_never_approve() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    pid = _invoke(e, iid, "propose_canon", novel_id=nid, scope="s",
                  payload=_PAYLOAD, rationale="r",
                  proposed_by="agent:sensitivity")["proposal_id"]
    assert pid                                     # proposing is fine
    assert _invoke(e, iid, "approve_canon", proposal_id=pid,
                   approver="agent:sensitivity",
                   approver_kind="managed_agent") is None   # denied
    assert _invoke(e, iid, "approve_canon", proposal_id=pid,
                   approver="") is None            # no anonymous approvals
    assert e.memory.recall(pid)["status"] == "proposal"     # untouched
    e.memory.close()
