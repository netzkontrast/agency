"""Acceptance — Spec 384 close-out: the report-render verb (analyze.report).

Closes 384's flagship scenario — the quality report RENDERS from the ported
templates (quality-report.md + iron-law-finding.md) rather than a print, and is a
round-trippable Document graph node (Spec 292). Audit-only sections (the Module
Dependency Graph) are gated by the template's `<!-- BEGIN IF is_audit -->` block,
honoured at render time.
"""
from __future__ import annotations

from conftest import invoke

_FINDINGS = [
    {"risk_code": "R2", "message": "Statement.summarize uses only Account's data",
     "source": "Fowler — Feature Envy", "consequence": "edits to Account ripple",
     "remedy": "move summarize onto Account", "tier": "warning"},
    {"risk_code": "R1", "message": "big() is 60 lines",
     "source": "McConnell — High-Quality Routines", "consequence": "hard to follow",
     "remedy": "extract cohesive blocks", "tier": "critical"},
]


def test_report_renders_from_template_as_a_document(engine, iid):
    r, _ = invoke(engine, iid, "analyze", "report",
                  mode="review", scope="src/", findings=_FINDINGS, score=80)
    content = r["content"]
    # the report shell came from quality-report.md
    assert "Quality Review — review" in content, content[:300]
    assert "80/100" in content
    # finding blocks came from iron-law-finding.md (the four-slot Iron Law form)
    assert "Symptom:" in content and "Source:" in content
    assert "Consequence:" in content and "Remedy:" in content
    assert "Statement.summarize uses only Account's data" in content
    # it is a round-trippable Document graph node (Spec 292)
    doc_id = r["document_id"]
    assert doc_id, r
    assert engine.memory.recall_typed(doc_id, "Document") is not None


def test_report_gates_the_audit_only_dependency_graph(engine, iid):
    review, _ = invoke(engine, iid, "analyze", "report",
                       mode="review", findings=_FINDINGS, score=90)
    audit, _ = invoke(engine, iid, "analyze", "report",
                      mode="audit", findings=_FINDINGS, score=90)
    # review: the BEGIN IF is_audit block is stripped — no graph section
    assert "Module Dependency Graph" not in review["content"], review["content"]
    # audit: the section + the mermaid graph render (derived from R5 findings)
    assert "Module Dependency Graph" in audit["content"]
    assert "graph TD" in audit["content"] and "```mermaid" in audit["content"]


def test_report_is_round_trippable_via_document(engine, iid):
    """The flagship round-trip: the rendered report persists as a Document keyed by
    a stable anchor (document.emit → _emit_graph_document), so a later document.sync
    of an on-disk edit reconciles keep-both (Spec 292)."""
    r, _ = invoke(engine, iid, "analyze", "report",
                  mode="debt", findings=_FINDINGS, score=70)
    doc = engine.memory.recall_typed(r["document_id"], "Document")
    assert doc is not None and doc.get("content_sha"), doc
