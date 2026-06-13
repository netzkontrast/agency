"""Spec 042 — Finding shape (the contract).

Every analyze.* axis returns a list of Finding value objects. The shape is
fixed; severity assignments are pinned per rule-id (Spec 042 §"Severity-
assignment rule per axis").

Spec 286 Phase 3 — the Finding is a frozen dataclass and severity a typed
``FindingSeverity`` str-enum (primitive-obsession → value object). The enum
subclasses ``str`` so a Finding stays JSON/wire-safe and ``f.severity ==
"warn"`` compares True against the legacy string values.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FindingSeverity(str, Enum):
    """Closed severity enum. Subclasses ``str`` so it serialises to the
    plain wire value ("info"/"warn"/"fail") and compares equal to it.

    Named ``FindingSeverity`` (not ``Severity``) to avoid colliding with
    the error-classification ``Severity`` in ``agency.toolresult``.
    """
    INFO = "info"
    WARN = "warn"
    FAIL = "fail"


_MSG_LIMIT = 120          # Spec 023 brief-budget
_EVIDENCE_LIMIT = 200     # Spec 023 evidence truncation


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: FindingSeverity
    file: str
    line: int
    message: str
    evidence: str


def make_finding(rule: str, severity: str, file: str, line: int,
                 message: str, evidence: str) -> Finding:
    """Construct a well-formed Finding with token-budget truncation
    applied. Severity is validated against the closed enum."""
    try:
        severity = FindingSeverity(severity)
    except ValueError:
        raise ValueError(
            f"severity must be info|warn|fail, got {severity!r}")
    return Finding(
        rule=rule,
        severity=severity,
        file=file,
        line=max(1, int(line)),
        message=message[:_MSG_LIMIT],
        evidence=evidence[:_EVIDENCE_LIMIT],
    )


def count_by_severity(findings: list[Finding]) -> dict[str, int]:
    """Tally findings into {info: int, warn: int, fail: int}."""
    counts = {"info": 0, "warn": 0, "fail": 0}
    for f in findings:
        # ``f.severity`` is a FindingSeverity (str subclass); its string
        # value keys the plain-string counts dict.
        s = str(f.severity.value)
        if s in counts:
            counts[s] += 1
    return counts
