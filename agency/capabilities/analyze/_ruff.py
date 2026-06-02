"""Spec 050 — ruff wrapper.

Composes ruff's 700+ Python lint rules into the agency Finding shape.
Degrades silently when ruff isn't on PATH (Spec 050 §"compose, don't
replace" — internal Q001-Q004 still fire in that case).

Subprocess + JSON; no Python-level ruff import (ruff is a Rust binary
anyway). Timeout 30s. Failure → empty list.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys

from ._findings import Finding, make_finding


# Ruff doesn't emit per-rule severity; we apply a fixed table.
# Default for unmapped codes = "warn". Add to this table by spec
# amendment.
_RUFF_SEVERITY: dict[str, str] = {
    # Pycodestyle errors (E*) — most are style; some structural.
    "E501": "warn",     # line-too-long
    "E701": "warn",     # multiple-statements-on-one-line-colon
    "E711": "warn",     # comparison-to-none
    "E712": "warn",     # comparison-to-true
    # Pyflakes (F*) — typically more substantive.
    "F401": "warn",     # unused-import
    "F811": "warn",     # redefined-while-unused
    "F841": "warn",     # unused-variable
    # Pep8-naming (N*) — info.
    "N801": "info",
    "N802": "info",
    "N803": "info",
    # Pyupgrade (UP*) — info.
    "UP001": "info",
}

_SUBPROCESS_TIMEOUT = 30.0


def scan(root: str) -> list[Finding]:
    """Run ruff over ``root``; return Findings. Empty list if ruff
    is not installed or the subprocess fails."""
    if shutil.which("ruff") is None:
        return []
    try:
        # Explicit --select so we don't rely on the user's
        # pyproject.toml ruff config (which may disable everything).
        # E + F = pycodestyle errors + pyflakes (the core code-quality
        # baseline). --line-length=100 matches our Q002 threshold so
        # findings stay consistent across paths.
        result = subprocess.run(
            ["ruff", "check", "--output-format=json",
             "--select", "E,F,W",
             "--line-length", "100",
             "--isolated",   # ignore user config; deterministic findings
             root],
            capture_output=True, text=True,
            timeout=_SUBPROCESS_TIMEOUT,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        print(f"ruff: subprocess failed ({exc!r})", file=sys.stderr)
        return []
    # ruff exits 0 (no findings) or 1 (findings present). Both are OK;
    # only exit codes > 1 indicate a real error.
    if result.returncode > 1:
        print(f"ruff: exited {result.returncode}: {result.stderr[:200]}",
              file=sys.stderr)
        return []
    try:
        payload = json.loads(result.stdout) if result.stdout else []
    except json.JSONDecodeError as exc:
        print(f"ruff: JSON parse failed ({exc})", file=sys.stderr)
        return []
    out: list[Finding] = []
    for item in payload:
        code = item.get("code") or "RUF"
        severity = _RUFF_SEVERITY.get(code, "warn")
        location = item.get("location") or {}
        line = int(location.get("row", 1))
        out.append(make_finding(
            rule=code,
            severity=severity,
            file=item.get("filename", ""),
            line=line,
            message=item.get("message", ""),
            evidence=item.get("url", "") or code,
        ))
    return out
