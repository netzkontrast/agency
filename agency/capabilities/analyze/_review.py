"""Shared review core (Spec 380): scope-detect · merge · Iron Law gate · classify.

This module is the single engine both develop.review (interactive) and
analyze.review (headless/CI) drive. The actors differ in pause behaviour, not
logic — pure functions here, no graph writes.
"""
from __future__ import annotations

import subprocess
from dataclasses import replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._findings import Finding


def scope_detect(scope: str = "") -> str:
    """Return the effective scope description (auto-detect from git state if empty)."""
    if scope:
        return scope
    try:
        r = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=2, check=False)
        if r.stdout.strip():
            return "staged changes"
        r2 = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True, text=True, timeout=2, check=False)
        if r2.stdout.strip():
            return "working tree changes"
        r3 = subprocess.run(
            ["git", "diff", "main...HEAD", "--name-only"],
            capture_output=True, text=True, timeout=2, check=False)
        if r3.stdout.strip():
            return "branch changes vs main"
    except Exception:
        pass
    return "whole repo"


def merge_findings(
    decidable: list["Finding"],
    judgment: list["Finding"],
) -> list["Finding"]:
    """Merge decidable + judgment — one Finding per (risk_code, file, line).

    Judgment enriches an existing decidable finding in place (consequence/remedy/
    sharper source); it creates a new Finding only where no decidable finding
    covers that (risk_code, span). Pure function; no graph writes (Hohpe fix).
    """
    out = list(decidable)
    index: dict[tuple, int] = {}
    for i, f in enumerate(out):
        if f.risk_code:
            index[(f.risk_code, f.file, f.line)] = i

    for jf in judgment:
        if jf.risk_code:
            key = (jf.risk_code, jf.file, jf.line)
            if key in index:
                i = index[key]
                existing = out[i]
                out[i] = replace(
                    existing,
                    consequence=jf.consequence or existing.consequence,
                    remedy=jf.remedy or existing.remedy,
                    source=jf.source or existing.source,
                )
            else:
                out.append(jf)
                index[key] = len(out) - 1
        else:
            out.append(jf)
    return out


def iron_law_passed(findings: list["Finding"]) -> bool:
    """Pure predicate: every brooks finding (non-empty risk_code) must carry
    both consequence AND remedy. This is the Iron Law gate — a decidable check
    over Finding fields, not agent self-assertion (Wiegers fix, Spec 380 §2).
    """
    return all(f.consequence and f.remedy for f in findings if f.risk_code)


def classify_remedy(finding: "Finding") -> str:
    """Classify a Finding's remedy as 'safe' (mechanical+local) or 'risky' (structural).

    Safe = can auto-apply; risky = structural change that needs human confirmation.
    """
    risky_keywords = [
        "invert", "move class", "move module", "restructure",
        "reorder", "split module", "decompose", "dependency direction",
        "invert dependency",
    ]
    remedy_lower = (getattr(finding, "remedy", "") or "").lower()
    for kw in risky_keywords:
        if kw in remedy_lower:
            return "risky"
    return "safe"


def quality_gate(score: int, critical: int,
                 min_score: int = 70, max_critical: int = 0) -> tuple[bool, str]:
    """The quality-gate decision (Spec 382 §2): PASSED iff ``score >= min_score``
    AND ``critical <= max_critical``. ``min_score`` / ``max_critical`` are
    documented tunable budgets (CLAUDE.md #8 — brooks-lint defaults), not magic
    snapshots. Returns ``(passed, evidence)`` — the evidence string is the
    auditable rationale recorded on the Gate node."""
    passed = score >= min_score and critical <= max_critical
    evidence = (f"score {score} (min {min_score}); "
                f"{critical} critical (max {max_critical})")
    return passed, evidence
