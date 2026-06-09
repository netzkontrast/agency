"""Novel cross-cap — 2 more tight-integration verbs (dogfood + analyze).

Extends the xcap surface (research/prompt/thinking already shipped) with
the remaining 2 core caps so criterion 8 holds: every novel slice carries
≥1 ctx.call to research / prompt / thinking / dogfood / analyze.

- record_storyform_decision(novel_id, decision, rationale) →
  delegates to dogfood.record_decision. Records the design choice with
  the storyform as `subject` for later cluster-wide decision audit.
- audit_novel_provenance(novel_id) → delegates to analyze.graph
  (node_type='Invocation') filtered for this novel's intent. Surfaces
  every cap that has SERVED the novel's work.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "novel xcap final") -> str:
    iid = e.intent.capture(purpose, "audit", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, cap: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, cap, verb, **kw)


def test_registers_two_more_xcap_verbs() -> None:
    e = _fresh()
    cap = e.registry._caps["novel"]
    assert {"record_storyform_decision", "audit_novel_provenance"} <= set(cap.verbs)
    e.memory.close()


# ─────────────────────── record_storyform_decision ───────────────────────


def test_record_storyform_decision_delegates_to_dogfood() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "novel", "create_novel",
                       title="X", author="Y")
    data, _ = _invoke(e, iid, "novel", "record_storyform_decision",
                      novel_id=novel["novel_id"],
                      decision="MC=changer, OS=Linear",
                      rationale="Per Dramatica linear-narrative canon")
    assert "decision" in data["decision_id"]  # dogfood emits 'decisionrecord:<hash>'
    # The dogfood-cap Invocation must SERVE the same intent.
    rows = e.memory.g.query(
        "MATCH (i:Invocation)-[r:SERVES]->(t:Intent) WHERE t.id = $iid "
        "AND i.capability = 'dogfood' RETURN i.verb",
        {"iid": iid})
    assert rows
    e.memory.close()


def test_record_storyform_decision_not_found() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "novel", "record_storyform_decision",
                        novel_id="novel:nope",
                        decision="x", rationale="y")
    assert data is None
    assert "NOT_FOUND" in e.memory.recall(inv).get("error", "")
    e.memory.close()


# ─────────────────────── audit_novel_provenance ───────────────────────


def test_audit_novel_provenance_lists_capabilities_via_analyze() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "novel", "create_novel",
                       title="X", author="Y")
    # Drive a few verbs to populate Invocations
    _invoke(e, iid, "novel", "capture_idea", text="something")
    _invoke(e, iid, "novel", "find_novel", query="X")
    data, _ = _invoke(e, iid, "novel", "audit_novel_provenance",
                      novel_id=novel["novel_id"])
    # Returns aggregated capability counts from analyze.graph census
    assert data["census"]["Invocation"] >= 3
    # The analyze-cap Invocation served the same intent.
    rows = e.memory.g.query(
        "MATCH (i:Invocation)-[r:SERVES]->(t:Intent) WHERE t.id = $iid "
        "AND i.capability = 'analyze' RETURN i.verb",
        {"iid": iid})
    assert rows
    e.memory.close()
