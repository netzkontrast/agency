"""Spec 050 — bandit wrapper.

Composes bandit's CWE-mapped Python security ruleset into the agency
Finding shape. Degrades silently when bandit isn't on PATH. The
subprocess scaffold lives in ``SubprocessAnalyzer`` (Spec 286); this module
supplies only the argv + payload mapping.
"""
from __future__ import annotations

# Spec 166 — external CLI tool + pip extra (derived wrapper registry).
EXTERNAL_TOOL = "bandit"
EXTERNAL_EXTRA = "analyze"

# Spec 057 — the rule prefixes this module's findings carry (axis registry).
AXIS_PREFIXES: dict[str, frozenset[str]] = {"security": frozenset({"B"})}

from ._findings import Finding, make_finding
from ._subprocess_analyzer import SubprocessAnalyzer


# bandit reports HIGH/MEDIUM/LOW severity AND confidence; agency Finding
# has one severity field. Map bandit's severity to agency's enum.
_BANDIT_SEVERITY: dict[str, str] = {
    "HIGH": "fail",
    "MEDIUM": "warn",
    "LOW": "info",
}


class _BanditAnalyzer(SubprocessAnalyzer):
    tool = "bandit"

    def argv(self, root: str) -> list[str]:
        # -q quiet (no banner), -f json output, -r recursive.
        return ["bandit", "-q", "-r", "-f", "json", root]

    def ok_returncode(self, rc: int) -> bool:
        # bandit exits 0 (no issues) or 1 (issues found). >1 = real error.
        return rc <= 1

    def empty_payload(self):
        return {}

    def map_payload(self, payload) -> list[Finding]:
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


def scan(root: str) -> list[Finding]:
    """Run bandit over ``root``; return Findings. Empty list if bandit
    is not installed or the subprocess fails."""
    return _BanditAnalyzer().run(root)
