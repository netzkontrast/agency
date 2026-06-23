"""Spec 393 — adr.draft(spec=…) creates the REFINES edge.

The deep-chain verifier found C14: a manually drafted+approved decision was never
recognized by `adr.spec_decisions_ready` (the /open→/inprogress hinge) because
`draft` stored `spec` as a node PROPERTY but never created the `REFINES` EDGE the
predicate traverses. This proves the manual draft lane now converges with the gate.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _inv(eng, iid):
    def call(cap, verb, **kw):
        return eng.registry.invoke(eng.memory, iid, cap, verb, **kw)[0]
    return call


def test_draft_with_spec_makes_the_decision_visible_to_the_hinge():
    eng = Engine(tempfile.mktemp(suffix=".db"))
    try:
        iid = eng.intent.capture("p", "d", "a")
        eng.intent.confirm(iid)
        inv = _inv(eng, iid)

        # a spec Document (Document requires path + content_sha)
        doc_id = eng.memory.record("Document",
                                   {"path": "Plan/x/spec.md", "content_sha": "abc123"})
        theme_id = inv("adr", "theme", layer="Workflow")["id"]

        # draft a decision tied to the spec — Spec 393 creates the REFINES edge
        d = inv("adr", "draft", theme_id=theme_id, decision="Do X because Y",
                spec=doc_id, context="prior art", facing="the choice",
                neglected="alt A, alt B", benefits="b", tradeoffs="t")
        did = d["id"]
        assert d["refines"] == doc_id, d        # the edge was created

        # BEFORE approval the decision IS recognized (not 'no-decisions') —
        # it just isn't approved yet.
        before = inv("adr", "spec_decisions_ready", spec_id=doc_id)
        assert before["ready"] is False
        # the C14 regression guard: the decision IS recognized (NOT 'no-decisions')
        assert before.get("reason") != "no-decisions", before
        assert before.get("blocking"), before     # it's listed as blocking (unapproved)

        # owner-approve (override the DoD gate) → the hinge clears
        inv("adr", "approve", decision_id=did, approver="user", override=True)
        after = inv("adr", "spec_decisions_ready", spec_id=doc_id)
        assert after["ready"] is True, after
    finally:
        eng.memory.close()
