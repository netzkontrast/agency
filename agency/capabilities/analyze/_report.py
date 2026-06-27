"""Spec 382 §4 / 384 / 388 — report-render helpers (tiering · summary · mermaid · the
quality-report render itself).

``analyze.report`` delegates here: ``render_quality_report`` builds the tier-sorted
finding view-dicts and hands them to ``ctx.render("quality-report", findings=…)`` —
the Jinja template (Spec 388) does the rest: ``{% if is_audit %}`` gates the Module
Dependency Graph, ``{% for f in findings %}`` loops each finding through the
``iron-law-finding`` form (``{% include %}``), and ``{# #}`` comments are
engine-stripped. The interim Spec 384 regex strippers (``<!-- BEGIN IF -->`` +
authoring-comment removal) are GONE — the engine evaluates the gates now. The
severity→tier vocabulary is single-sourced from ``_score`` (rule 2 — not a fourth
copy). Pure except ``render_quality_report``, which takes a ctx for ``ctx.render``.
"""
from __future__ import annotations

from collections import Counter

from ._score import _tier_of            # single source for the severity→tier read

_TIER_ORDER = ["critical", "warning", "suggestion"]


def tier_sorted(findings: list) -> list:
    """Findings ordered critical → warning → suggestion (the report's render order)."""
    order = {t: i for i, t in enumerate(_TIER_ORDER)}
    return sorted(findings, key=lambda f: order.get(_tier_of(f), len(_TIER_ORDER)))


def mermaid_graph(findings: list) -> str:
    """The mermaid Module Dependency Graph BODY for audit mode (R5 import cycles).
    Just the fenced block — the template owns the ``## Module Dependency Graph``
    heading inside its ``<!-- BEGIN IF is_audit -->`` gate (no double heading)."""
    cycles = [f for f in findings if f.get("risk_code") == "R5"]
    body = ("\n".join(f"  %% {f.get('file', '')}: {f.get('message', '')}"
                      for f in cycles)
            or "  %% no module-dependency findings")
    return "```mermaid\ngraph TD\n" + body + "\n```"


def summary(findings: list, score: int) -> str:
    """The one-line Summary — counts the tiers in a SINGLE pass (``_tier_of`` once
    per finding), no throwaway per-tier lists."""
    n = Counter(_tier_of(f) for f in findings)
    c, w, s = n["critical"], n["warning"], n["suggestion"]
    lead = ("Address the critical findings first." if c
            else "No critical findings; tighten the warnings." if w
            else "Only minor suggestions remain." if s
            else "Clean — no findings.")
    return f"{c} critical, {w} warning, {s} suggestion. {lead}"


def _finding_view(f: dict) -> dict:
    """One finding as the view-dict the ``iron-law-finding`` form expects — the
    wire-shape→template-slot mapping (risk_code→risk_name, file:line→title, etc.).
    Pure data prep; the template composes the prose."""
    rid = f.get("risk_code") or f.get("rule", "") or "Finding"
    loc = ":".join(str(x) for x in (f.get("file", ""), f.get("line", "")) if x)
    return {
        "risk_name": rid,
        "title": loc or "finding",
        "symptom": f.get("message", "") or f.get("evidence", ""),
        "source": f.get("source", ""),
        "consequence": f.get("consequence", ""),
        "remedy": f.get("remedy", ""),
        "fix_tier_label": "",
    }


def render_quality_report(ctx, findings: list, mode: str = "review",
                          scope: str = "", score: int = 100) -> str:
    """Render the Iron-Law quality report through the Jinja ``quality-report``
    template (Spec 388): hand it the tier-sorted finding view-dicts and the
    ``is_audit`` flag, and the template evaluates the ``{% if is_audit %}`` gate +
    loops each finding through ``iron-law-finding`` (``{% include %}``). No manual
    block-join, no post-strip — the engine composes the list and strips its own
    ``{# #}`` comments. Returns the finalized markdown — ``analyze.report`` persists
    it via ``document.emit``."""
    return ctx.render(
        "quality-report", mode=mode, scope=scope or "repo", score=score,
        is_audit=mode == "audit", trend_suffix="", config_line="", verdict="",
        module_graph=mermaid_graph(findings) if mode == "audit" else "",
        findings=[_finding_view(f) for f in tier_sorted(findings)],
        suppressed_block="", summary=summary(findings, score))
