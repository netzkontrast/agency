"""Spec 050 — ruff wrapper.

Composes ruff's 700+ Python lint rules into the agency Finding shape.
Degrades silently when ruff isn't on PATH (Spec 050 §"compose, don't
replace" — internal Q001-Q004 still fire in that case).

Subprocess + JSON; no Python-level ruff import (ruff is a Rust binary
anyway). Timeout 30s. Failure → empty list. The which-guard / run /
returncode / JSON-parse scaffold lives in ``SubprocessAnalyzer`` (Spec 286);
this module supplies only the argv + payload mapping.
"""
from __future__ import annotations

# Spec 166 — the external CLI tool this wrapper shells out to + the pip extra it
# ships under, so the wrapper registry (derive_wrapper_shapes) + the doctor's
# analyze_extras DERIVE from the modules instead of a hand-listed tuple.
EXTERNAL_TOOL = "ruff"
EXTERNAL_EXTRA = "analyze"

# Spec 057 — ruff codes this wrapper emits, all mapped to quality (longest-first in registry).
AXIS_PREFIXES: dict[str, frozenset[str]] = {
    "quality": frozenset({"E", "F", "W", "I", "C", "N", "UP", "D",
                          "PL", "PT", "RUF", "SIM", "RET", "TRY"}),
}

from ._findings import Finding, make_finding
from ._subprocess_analyzer import SubprocessAnalyzer


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


class _RuffAnalyzer(SubprocessAnalyzer):
    tool = "ruff"

    def argv(self, root: str) -> list[str]:
        # Explicit --select so we don't rely on the user's pyproject.toml
        # ruff config (which may disable everything). E + F = pycodestyle
        # errors + pyflakes (the core code-quality baseline).
        # --line-length=100 matches our Q002 threshold so findings stay
        # consistent across paths. --isolated ignores user config →
        # deterministic findings (Spec 042).
        return ["ruff", "check", "--output-format=json",
                "--select", "E,F,W",
                "--line-length", "100",
                "--isolated",
                root]

    def ok_returncode(self, rc: int) -> bool:
        # ruff exits 0 (no findings) or 1 (findings present). Both OK;
        # only exit codes > 1 indicate a real error.
        return rc <= 1

    def empty_payload(self):
        return []

    def map_payload(self, payload) -> list[Finding]:
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


def scan(root: str) -> list[Finding]:
    """Run ruff over ``root``; return Findings. Empty list if ruff
    is not installed or the subprocess fails.

    Note: invoked with ``--isolated`` so the caller's ``pyproject.toml``
    ruff config is DELIBERATELY ignored — Spec 042 demands findings be
    deterministic across paths. The fixed rule set is `E,F,W` with
    ``--line-length=100``. Users who want to customize ruff should
    run it standalone outside the analyze capability.
    """
    return _RuffAnalyzer().run(root)
