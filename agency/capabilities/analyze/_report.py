"""Spec 382 §4 / 384 — report-render helpers (tiering · summary · mermaid body).

The report RENDER PATH adopted the Spec 060 templates in Spec 384: ``analyze.report``
renders ``quality-report.md`` + ``iron-law-finding.md`` via ``ctx.render`` and
persists the result as a round-trippable ``Document`` (``document.emit``). These
pure helpers supply the bits the template can't compute — the tier ordering, the
one-line Summary, and the mermaid graph BODY (the template owns the heading + the
audit `<!-- BEGIN IF is_audit -->` gate). Pure — no graph writes.
"""
from __future__ import annotations

_TIER_ORDER = ["critical", "warning", "suggestion"]
_SEVERITY_TIER = {"fail": "critical", "warn": "warning", "info": "suggestion"}


def _tier(f: dict) -> str:
    return f.get("tier") or _SEVERITY_TIER.get(str(f.get("severity", "")), "suggestion")


def tier_sorted(findings: list) -> list:
    """Findings ordered critical → warning → suggestion (the report's render order)."""
    order = {t: i for i, t in enumerate(_TIER_ORDER)}
    return sorted(findings, key=lambda f: order.get(_tier(f), len(_TIER_ORDER)))


def mermaid_graph(findings: list) -> str:
    """The mermaid Module Dependency Graph BODY for audit mode (R5 import cycles).
    Just the fenced block — the template supplies the ``## Module Dependency Graph``
    heading inside its `<!-- BEGIN IF is_audit -->` gate (no double heading)."""
    cycles = [f for f in findings if f.get("risk_code") == "R5"]
    body = ("\n".join(f"  %% {f.get('file', '')}: {f.get('message', '')}"
                      for f in cycles)
            or "  %% no module-dependency findings")
    return "```mermaid\ngraph TD\n" + body + "\n```"


def summary(findings: list, score: int) -> str:
    by = {t: [f for f in findings if _tier(f) == t] for t in _TIER_ORDER}
    c, w, s = len(by["critical"]), len(by["warning"]), len(by["suggestion"])
    lead = ("Address the critical findings first." if c
            else "No critical findings; tighten the warnings." if w
            else "Only minor suggestions remain." if s
            else "Clean — no findings.")
    return f"{c} critical, {w} warning, {s} suggestion. {lead}"
