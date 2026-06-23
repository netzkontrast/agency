"""Spec 382 §4 / 384 — report-render helpers (tiering · summary · mermaid · the
quality-report render itself).

``analyze.report`` delegates here: ``render_quality_report`` renders the Spec 384
templates (``quality-report.md`` + ``iron-law-finding.md`` via ``ctx.render``) and
applies the INTERIM ``<!-- BEGIN IF -->`` / authoring-comment processing — Spec 388
replaces this whole strip path with a Jinja ``{% if %}`` engine, a one-file delete
here. The severity→tier vocabulary is single-sourced from ``_score`` (rule 2 — not a
fourth copy). Pure except ``render_quality_report``, which takes a ctx for
``ctx.render``.
"""
from __future__ import annotations

import re
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


# ── interim template conditional / comment processing (Spec 388 → Jinja) ───────
# Nothing evaluates the template ``<!-- BEGIN IF flag -->…<!-- END IF -->`` markers
# (string.Template only substitutes $vars). These honour them programmatically until
# Spec 388 ports the templates to Jinja ``{% if %}`` and DELETES this whole block +
# the two strip calls in render_quality_report.
_COND_RE = re.compile(r"[ \t]*<!-- BEGIN IF (\w+) -->\n?(.*?)<!-- END IF -->\n?",
                      re.DOTALL)
_COMMENT_RE = re.compile(r"[ \t]*<!-- (?:AGENT|doc-source):.*?-->\n?", re.DOTALL)


def strip_conditionals(text: str, flags: dict) -> str:
    """Keep a ``<!-- BEGIN IF flag -->…<!-- END IF -->`` block's inner content when
    ``flag`` is truthy, drop the whole block otherwise."""
    return _COND_RE.sub(lambda m: m.group(2) if flags.get(m.group(1)) else "", text)


def strip_comments(text: str) -> str:
    """Drop the Spec-060 authoring annotations (AGENT / doc-source) from the FINAL
    output — they guide the template author, not the report reader. The template
    FILES keep their markers (drift-tracked by check-doc-drift)."""
    return _COMMENT_RE.sub("", text)


def render_quality_report(ctx, findings: list, mode: str = "review",
                          scope: str = "", score: int = 100) -> str:
    """Render the Iron-Law quality report from the Spec 384 templates: each finding
    via ``iron-law-finding.md``, the shell via ``quality-report.md`` (``ctx.render``),
    then honour the audit-only ``<!-- BEGIN IF is_audit -->`` gate + strip the
    authoring comments. Returns the finalized markdown — ``analyze.report`` persists
    it via ``document.emit``."""
    blocks = []
    for f in tier_sorted(findings):
        rid = f.get("risk_code") or f.get("rule", "") or "Finding"
        loc = ":".join(str(x) for x in (f.get("file", ""), f.get("line", "")) if x)
        blocks.append(ctx.render(
            "iron-law-finding", risk_name=rid, title=loc or "finding",
            symptom=f.get("message", "") or f.get("evidence", ""),
            source=f.get("source", ""), consequence=f.get("consequence", ""),
            remedy=f.get("remedy", ""), fix_tier_label=""))
    rendered = ctx.render(
        "quality-report", mode=mode, scope=scope or "repo", score=score,
        trend_suffix="", config_line="", verdict="",
        module_graph=mermaid_graph(findings) if mode == "audit" else "",
        findings_block="\n\n".join(blocks), suppressed_block="",
        summary=summary(findings, score))
    return strip_comments(
        strip_conditionals(rendered, {"is_audit": mode == "audit"}))
