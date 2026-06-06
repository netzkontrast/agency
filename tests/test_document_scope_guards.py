"""Spec 056 follow-up (PR #22 review) — render's for_intent_id label-check is
scope-aware, and analyze.paths' root_intent_id is label-checked.

`document.render(scope='research-report', for_intent_id=)` forwards the param as
a *Research* id (research.lead's output), so an Intent-only guard would break the
deep-research publish path. The guard must expect Intent for provenance/
reflections and Research for research-report.
"""
from __future__ import annotations

import tempfile
import types

from agency.capabilities.analyze import _paths
from agency.capabilities.plugin._main import _check_node_id_guards
from agency.engine import Engine


def _engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = e.intent.capture("p", "d", "a")
    e.intent.confirm(iid)
    return e, iid


def _call(e, iid, verb, **kw):
    res, _ = e.registry.invoke(e.memory, iid, "document", verb, **kw)
    return res["result"] if isinstance(res, dict) and "result" in res else res


def test_research_report_accepts_a_research_id():
    e, iid = _engine()
    try:
        lead, _ = e.registry.invoke(e.memory, iid, "research", "lead",
                                    question="what is X?", depth="brief")
        rid = (lead.get("result") or lead)["research_id"]
        out = _call(e, iid, "render", scope="research-report", for_intent_id=rid)
        # the Research id must NOT be rejected as a non-Intent
        assert "is not an Intent id" not in (out.get("error") or "")
        assert out.get("error") is None or "Research" not in out.get("error", "")
    finally:
        e.memory.close()


def test_research_report_rejects_non_research_id():
    e, iid = _engine()
    try:
        out = _call(e, iid, "render", scope="research-report", for_intent_id=iid)  # iid is an Intent
        assert "not a Research id" in (out.get("error") or "")
    finally:
        e.memory.close()


def test_provenance_rejects_non_intent_id():
    e, iid = _engine()
    try:
        aid = e.memory.record("Artefact", {"kind": "x"})
        out = _call(e, iid, "render", scope="provenance", for_intent_id=aid)
        assert "not an Intent id" in (out.get("error") or "")
    finally:
        e.memory.close()


def test_provenance_accepts_intent_id():
    e, iid = _engine()
    try:
        out = _call(e, iid, "render", scope="provenance", for_intent_id=iid)
        assert "not an Intent id" not in (out.get("error") or "")
    finally:
        e.memory.close()


def test_paths_scan_rejects_non_intent_root():
    e, iid = _engine()
    try:
        aid = e.memory.record("Artefact", {"kind": "x"})  # not an Intent
        findings = _paths.scan(e.memory, root_intent_id=aid)
        assert findings == []  # no mis-scoped scan on a wrong-label root
    finally:
        e.memory.close()


def test_lint_table_covers_root_intent_id():
    def _verb(self, root_intent_id: str):
        return memory.recall(root_intent_id)  # noqa: F821 — bare recall anti-pattern

    cap = types.SimpleNamespace(verbs={"paths": {"fn": _verb, "role": "transform"}})
    findings = _check_node_id_guards(cap)
    assert any(f["kind"] == "node_id_guard" and "Intent" in f["msg"] for f in findings)
