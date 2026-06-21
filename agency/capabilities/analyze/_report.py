"""Spec 382 §4 — the Iron-Law report render path (structured findings → markdown).

Projects the structured findings into the human-readable report: a header with
the Health Score, findings sorted by tier (critical→warning→suggestion) each as
the Iron Law block (Symptom / Source / Consequence / Remedy), empty tiers
omitted, a mermaid Module Dependency Graph in audit mode (R5), and a Summary.

The render PATH lives here; the template FILE (Spec 060 `<!-- AGENT: -->`) is
authored in Spec 384 and adopted via `document.render` then. Pure — no graph
writes.
"""
from __future__ import annotations

_TIER_ORDER = ["critical", "warning", "suggestion"]
_SEVERITY_TIER = {"fail": "critical", "warn": "warning", "info": "suggestion"}


def _tier(f: dict) -> str:
    return f.get("tier") or _SEVERITY_TIER.get(str(f.get("severity", "")), "suggestion")


def _mermaid(findings: list) -> list[str]:
    """A Module Dependency Graph for audit mode — R5 import-cycle findings."""
    cycles = [f for f in findings if f.get("risk_code") == "R5"]
    body = ("\n".join(f"  %% {f.get('file', '')}: {f.get('message', '')}"
                      for f in cycles)
            or "  %% no module-dependency findings")
    return ["## Module Dependency Graph", "```mermaid", "graph TD", body, "```", ""]


def _summary(by_tier: dict, score: int) -> str:
    c, w, s = (len(by_tier["critical"]), len(by_tier["warning"]),
               len(by_tier["suggestion"]))
    lead = ("Address the critical findings first." if c
            else "No critical findings; tighten the warnings." if w
            else "Only minor suggestions remain." if s
            else "Clean — no findings.")
    return f"Health Score {score}/100 — {c} critical, {w} warning, {s} suggestion. {lead}"


def render_report(findings: list, mode: str = "review", scope: str = "",
                  score: int = 100) -> str:
    """Render the Iron-Law report markdown from structured findings."""
    out = [f"# Code Quality Report — {mode}",
           f"**Scope:** {scope or 'repo'} · **Health Score:** {score}/100", ""]
    by_tier = {t: [f for f in findings if _tier(f) == t] for t in _TIER_ORDER}
    for t in _TIER_ORDER:
        fs = by_tier[t]
        if not fs:
            continue                       # empty tiers omitted
        out.append(f"## {t.capitalize()} ({len(fs)})")
        for f in fs:
            rid = f.get("risk_code") or f.get("rule", "")
            out.append(f"### {rid} — {f.get('file', '')}:{f.get('line', '')}")
            out.append(f"- **Symptom:** {f.get('message', '')}")
            if f.get("source"):
                out.append(f"- **Source:** {f['source']}")
            if f.get("consequence"):
                out.append(f"- **Consequence:** {f['consequence']}")
            if f.get("remedy"):
                out.append(f"- **Remedy:** {f['remedy']}")
            out.append("")
    if mode == "audit":
        out += _mermaid(findings)
    out += ["## Summary", _summary(by_tier, score)]
    return "\n".join(out)
