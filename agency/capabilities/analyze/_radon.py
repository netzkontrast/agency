"""Spec 050 — radon wrapper.

Composes radon's cyclomatic complexity + maintainability index into
the agency Finding shape. Q005 = cyclomatic > 12 (rank C+); Q006 =
maintainability index < 65. Degrades silently when radon missing.
"""
from __future__ import annotations

# Spec 057 — radon rides on quality's Q prefix; declares none (symmetry).
AXIS_PREFIXES: dict[str, frozenset[str]] = {}

import json
import shutil
import subprocess
import sys

from ._findings import Finding, make_finding


# radon's CC rank → agency severity. A/B (≤10) not reported.
_RADON_CC_SEVERITY: dict[str, str | None] = {
    "A": None,    # 0-5 — clean
    "B": None,    # 6-10 — okay
    "C": "warn",  # 11-20 — moderate
    "D": "warn",  # 21-30 — complex
    "E": "fail",  # 31-40 — very complex
    "F": "fail",  # 41+ — refactor candidate
}

_SUBPROCESS_TIMEOUT = 30.0
_MI_LOW_THRESHOLD = 65.0   # Spec 050 §"radon MI threshold" — defer override to v2


def cyclomatic(root: str) -> list[Finding]:
    """Run `radon cc -j` over ``root``; emit Q005 findings for
    rank ≥ C (complexity > 10). Empty list when radon missing."""
    if shutil.which("radon") is None:
        return []
    try:
        result = subprocess.run(
            ["radon", "cc", "-j", "-s", root],   # -s = include score
            capture_output=True, text=True,
            timeout=_SUBPROCESS_TIMEOUT,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        print(f"radon cc: subprocess failed ({exc!r})", file=sys.stderr)
        return []
    if result.returncode != 0:
        print(f"radon cc: exited {result.returncode}", file=sys.stderr)
        return []
    try:
        payload = json.loads(result.stdout) if result.stdout else {}
    except json.JSONDecodeError as exc:
        print(f"radon cc: JSON parse failed ({exc})", file=sys.stderr)
        return []
    out: list[Finding] = []
    for filename, items in payload.items():
        for item in items:
            rank = item.get("rank", "A")
            severity = _RADON_CC_SEVERITY.get(rank)
            if severity is None:
                continue
            name = item.get("name", "<anon>")
            complexity = item.get("complexity", 0)
            out.append(make_finding(
                rule=f"Q005-{rank}",
                severity=severity,
                file=filename,
                line=int(item.get("lineno", 1)),
                message=f"cyclomatic complexity {complexity} (rank {rank}) "
                        f"in {name!r} — consider refactoring",
                evidence=f"{name} (CC={complexity})",
            ))
    return out


def maintainability(root: str) -> list[Finding]:
    """Run `radon mi -j` over ``root``; emit Q006 findings for low MI."""
    if shutil.which("radon") is None:
        return []
    try:
        result = subprocess.run(
            ["radon", "mi", "-j", "-s", root],   # -s = include score
            capture_output=True, text=True,
            timeout=_SUBPROCESS_TIMEOUT,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        print(f"radon mi: subprocess failed ({exc!r})", file=sys.stderr)
        return []
    if result.returncode != 0:
        return []
    try:
        payload = json.loads(result.stdout) if result.stdout else {}
    except json.JSONDecodeError:
        return []
    out: list[Finding] = []
    for filename, info in payload.items():
        if not isinstance(info, dict):
            continue
        mi = info.get("mi", 100.0)
        rank = info.get("rank", "A")
        if mi >= _MI_LOW_THRESHOLD:
            continue
        # Below-threshold MI is the Q006 signal — every rank in this
        # branch is a maintainability concern. C (the lowest rank
        # radon emits) escalates to fail; A/B/below-threshold stay at
        # warn. The previous mapping demoted A/C to info, which
        # under-counted the very findings Q006 is meant to surface.
        if rank == "C":
            sev = "fail"
        else:
            sev = "warn"
        out.append(make_finding(
            rule="Q006",
            severity=sev,
            file=filename, line=1,
            message=f"maintainability index {mi:.1f} (rank {rank}) — "
                    "split or refactor",
            evidence=f"MI={mi:.1f}",
        ))
    return out
