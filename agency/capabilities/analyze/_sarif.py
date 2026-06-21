"""Spec 382 §1 — SARIF 2.1.0 emit, straight from structured Findings.

Agency findings are born structured (Spec 360 ``Finding`` nodes), so SARIF renders
with NO parsing step — brooks-lint's ``report-parse.mjs`` is dropped. The rule set
is DERIVED from the live decay-risk registry (``decay-risks.json`` + any custom
``Cx``), never a pinned list (rule 8), so it cannot drift. The emit is capped with
a truncation locator (CLAUDE.md #9 — count + "N of M shown", never a silent drop;
the full finding set stays in the graph).
"""
from __future__ import annotations

import hashlib

SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
SARIF_VERSION = "2.1.0"

# tier (Spec 360 §1) → SARIF result level.
_TIER_LEVEL = {"critical": "error", "warning": "warning", "suggestion": "note"}
# severity → tier, when a wire finding doesn't carry a derived ``tier``.
_SEVERITY_TIER = {"fail": "critical", "warn": "warning", "info": "suggestion"}


def _tier(f: dict) -> str:
    return f.get("tier") or _SEVERITY_TIER.get(str(f.get("severity", "")), "suggestion")


def _fingerprint(f: dict) -> str:
    """Stable across runs (rule+file+symptom) so code-scanning dedups."""
    raw = f"{f.get('risk_code') or f.get('rule', '')}|{f.get('file', '')}|{f.get('message', '')}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _rules(risks: dict) -> list[dict]:
    """One ``reportingDescriptor`` per risk code — DERIVED from the registry."""
    rules = []
    for code in sorted(risks):
        e = risks[code]
        rules.append({
            "id": code,
            "name": e.get("name", code),
            "shortDescription": {"text": e.get("diagnostic", e.get("name", code))},
            "properties": {
                "sources": [f"{s.get('book', '')} — {s.get('principle', '')}"
                            for s in e.get("sources", [])],
            },
        })
    return rules


def _message(f: dict) -> str:
    """The Iron Law as the SARIF message: Symptom (+ Consequence + Remedy)."""
    parts = [f.get("message", "")]
    if f.get("consequence"):
        parts.append(f"Consequence: {f['consequence']}")
    if f.get("remedy"):
        parts.append(f"Remedy: {f['remedy']}")
    return "\n\n".join(p for p in parts if p)


def _result(f: dict) -> dict:
    return {
        "ruleId": f.get("risk_code") or f.get("rule", ""),
        "level": _TIER_LEVEL.get(_tier(f), "note"),
        "message": {"text": _message(f)},
        "locations": [{"physicalLocation": {
            "artifactLocation": {"uri": f.get("file", "")},
            "region": {"startLine": max(1, int(f.get("line", 1) or 1))}}}],
        "partialFingerprints": {"agencyFindingHash/v1": _fingerprint(f)},
    }


def to_sarif(findings: list, risks: dict, max_results: int | None = None,
             tool_name: str = "agency-analyze") -> tuple[dict, int, bool]:
    """Render ``findings`` as a SARIF 2.1.0 document. Returns
    ``(doc, total, truncated)``; when ``max_results`` caps the set the run carries
    a ``properties.truncated`` locator ("N of M shown")."""
    total = len(findings)
    capped = list(findings[:max_results]) if max_results else list(findings)
    run: dict = {
        "tool": {"driver": {
            "name": tool_name,
            "informationUri": "https://github.com/netzkontrast/agency",
            "rules": _rules(risks),
        }},
        "results": [_result(f) for f in capped],
    }
    truncated = max_results is not None and total > max_results
    if truncated:
        run["properties"] = {"truncated": f"{len(capped)} of {total} shown"}
    doc = {"$schema": SARIF_SCHEMA, "version": SARIF_VERSION, "runs": [run]}
    return doc, total, truncated
