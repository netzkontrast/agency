"""Spec 050 — bandit wrapper.

Composes bandit's CWE-mapped Python security ruleset into the agency
Finding shape. Degrades silently when bandit isn't on PATH.
"""
from __future__ import annotations

# Spec 057 — the rule prefixes this module's findings carry (axis registry).
AXIS_PREFIXES: dict[str, frozenset[str]] = {"security": frozenset({"B"})}

import json
import shutil
import subprocess
import sys

from ._findings import Finding, make_finding


# bandit reports HIGH/MEDIUM/LOW severity AND confidence; agency Finding
# has one severity field. Map bandit's severity to agency's enum.
_BANDIT_SEVERITY: dict[str, str] = {
    "HIGH": "fail",
    "MEDIUM": "warn",
    "LOW": "info",
}

_SUBPROCESS_TIMEOUT = 30.0


def scan(root: str) -> list[Finding]:
    """Run bandit over ``root``; return Findings. Empty list if bandit
    is not installed or the subprocess fails."""
    if shutil.which("bandit") is None:
        return []
    try:
        # -q quiet (no banner), -f json output, -r recursive.
        result = subprocess.run(
            ["bandit", "-q", "-r", "-f", "json", root],
            capture_output=True, text=True,
            timeout=_SUBPROCESS_TIMEOUT,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        print(f"bandit: subprocess failed ({exc!r})", file=sys.stderr)
        return []
    # bandit exits 0 (no issues) or 1 (issues found). >1 = real error.
    if result.returncode > 1:
        print(f"bandit: exited {result.returncode}: {result.stderr[:200]}",
              file=sys.stderr)
        return []
    try:
        payload = json.loads(result.stdout) if result.stdout else {}
    except json.JSONDecodeError as exc:
        print(f"bandit: JSON parse failed ({exc})", file=sys.stderr)
        return []
    out: list[Finding] = []
    for item in payload.get("results", []):
        sev = _BANDIT_SEVERITY.get(
            (item.get("issue_severity") or "MEDIUM").upper(), "warn")
        out.append(make_finding(
            rule=item.get("test_id", "B000"),
            severity=sev,
            file=item.get("filename", ""),
            line=int(item.get("line_number", 1) or 1),
            message=item.get("issue_text", ""),
            evidence=(item.get("code", "") or "").strip(),
        ))
    return out
