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

from agency._capture import keep_full


class FindingSeverity(str, Enum):
    """Closed severity enum. Subclasses ``str`` so it serialises to the
    plain wire value ("info"/"warn"/"fail") and compares equal to it.

    Named ``FindingSeverity`` (not ``Severity``) to avoid colliding with
    the error-classification ``Severity`` in ``agency.toolresult``.
    """
    INFO = "info"
    WARN = "warn"
    FAIL = "fail"


# Spec 354 — the brooks-lint severity vocabulary is a DERIVED view of the
# canonical enum, never a second stored field (rule 2 / rule 8). One mapping,
# computed on read by ``Finding.tier``.
_SEVERITY_TIER = {
    FindingSeverity.FAIL: "critical",
    FindingSeverity.WARN: "warning",
    FindingSeverity.INFO: "suggestion",
}


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
    # ── Spec 354 Iron Law extension (all optional → backward-compatible) ──
    # An empty ``risk_code`` is a pure-decidable analyze finding (today's
    # behaviour); a non-empty ``risk_code`` is a brooks decay finding carrying
    # the full Iron Law: Symptom (message/evidence) → Source → Consequence →
    # Remedy.
    risk_code: str = ""    # "R1".."R6", "T1".."T6", or a defined custom "Cx"
    source: str = ""       # the Iron Law Source: "Book — Principle/Smell"
    consequence: str = ""  # what decays if left unfixed
    remedy: str = ""       # the concrete corrective action

    @property
    def tier(self) -> str:
        """The brooks-lint severity vocabulary (critical/warning/suggestion),
        DERIVED from the canonical ``FindingSeverity`` — never stored (rule 2 /
        rule 8). analyze scores info/warn/fail (the wire value); reports and the
        Health Score (Spec 356) render this tier."""
        return _SEVERITY_TIER[FindingSeverity(self.severity)]

    def to_dict(self) -> dict:
        """The wire/graph representation: a plain dict with severity as its
        string value. Spec 286's six-key contract is preserved; Spec 354 grows
        it ADDITIVELY with the four Iron Law keys (empty string when this is a
        plain decidable finding, so the wire shape stays stable)."""
        return {
            "rule": self.rule,
            "severity": self.severity.value,
            "file": self.file,
            "line": self.line,
            "message": self.message,
            "evidence": self.evidence,
            "risk_code": self.risk_code,
            "source": self.source,
            "consequence": self.consequence,
            "remedy": self.remedy,
        }


def make_finding(rule: str, severity: str, file: str, line: int,
                 message: str, evidence: str,
                 risk_code: str = "", source: str = "",
                 consequence: str = "", remedy: str = "") -> Finding:
    """Construct a well-formed Finding. Severity is validated against the closed
    enum; message/evidence keep their Spec 023 token-budget truncation (the wire
    preview). The Spec 354 Iron Law fields are optional and, per CLAUDE.md #9,
    captured DATA — source/consequence/remedy are kept in FULL via ``keep_full``
    (warn-not-cut), never sliced to the message/evidence budget."""
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
        risk_code=risk_code,
        source=keep_full(source, label="finding.source"),
        consequence=keep_full(consequence, label="finding.consequence"),
        remedy=keep_full(remedy, label="finding.remedy"),
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
