"""Spec 042 — Finding shape (the contract).

Every analyze.* axis returns a list of Finding dicts. The shape is
fixed; severity assignments are pinned per rule-id (Spec 042 §"Severity-
assignment rule per axis").
"""
from __future__ import annotations

from typing import TypedDict


_SEVERITIES = frozenset({"info", "warn", "fail"})

_MSG_LIMIT = 120          # Spec 023 brief-budget
_EVIDENCE_LIMIT = 200     # Spec 023 evidence truncation


class Finding(TypedDict):
    rule: str
    severity: str
    file: str
    line: int
    message: str
    evidence: str


def make_finding(rule: str, severity: str, file: str, line: int,
                 message: str, evidence: str) -> Finding:
    """Construct a well-formed Finding with token-budget truncation
    applied. Severity is validated against the closed enum."""
    if severity not in _SEVERITIES:
        raise ValueError(f"severity must be info|warn|fail, got {severity!r}")
    return {
        "rule": rule,
        "severity": severity,
        "file": file,
        "line": max(1, int(line)),
        "message": message[:_MSG_LIMIT],
        "evidence": evidence[:_EVIDENCE_LIMIT],
    }


def count_by_severity(findings: list[Finding]) -> dict[str, int]:
    """Tally findings into {info: int, warn: int, fail: int}."""
    counts = {"info": 0, "warn": 0, "fail": 0}
    for f in findings:
        s = f.get("severity", "info")
        if s in counts:
            counts[s] += 1
    return counts
