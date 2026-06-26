"""Spec 050 — radon wrapper.

Composes radon's cyclomatic complexity + maintainability index into
the agency Finding shape. Q005 = cyclomatic > 12 (rank C+); Q006 =
maintainability index < 65. Degrades silently when radon missing. The
subprocess scaffold lives in ``SubprocessAnalyzer`` (Spec 286); this module
supplies the two argvs + payload mappings (one analyzer per radon sub-command).
"""
from __future__ import annotations

# Spec 166 — external CLI tool + pip extra (derived wrapper registry).
EXTERNAL_TOOL = "radon"
EXTERNAL_EXTRA = "analyze"

# Spec 057 — radon rides on quality's Q prefix; declares none (symmetry).
AXIS_PREFIXES: dict[str, frozenset[str]] = {}

from ._findings import Finding, make_finding
from ._subprocess_analyzer import SubprocessAnalyzer


# radon's CC rank → agency severity. A/B (≤10) not reported.
_RADON_CC_SEVERITY: dict[str, str | None] = {
    "A": None,    # 0-5 — clean
    "B": None,    # 6-10 — okay
    "C": "warn",  # 11-20 — moderate
    "D": "warn",  # 21-30 — complex
    "E": "fail",  # 31-40 — very complex
    "F": "fail",  # 41+ — refactor candidate
}

_MI_LOW_THRESHOLD = 65.0   # Spec 050 §"radon MI threshold" — defer override to v2


class _RadonCCAnalyzer(SubprocessAnalyzer):
    tool = "radon"
    label = "radon cc"

    def argv(self, root: str) -> list[str]:
        return ["radon", "cc", "-j", "-s", root]   # -s = include score

    def ok_returncode(self, rc: int) -> bool:
        return rc == 0

    def empty_payload(self):
        return {}

    def map_payload(self, payload) -> list[Finding]:
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


class _RadonMIAnalyzer(SubprocessAnalyzer):
    tool = "radon"
    label = "radon mi"

    def argv(self, root: str) -> list[str]:
        return ["radon", "mi", "-j", "-s", root]   # -s = include score

    def ok_returncode(self, rc: int) -> bool:
        return rc == 0

    def empty_payload(self):
        return {}

    def map_payload(self, payload) -> list[Finding]:
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
            # warn.
            sev = "fail" if rank == "C" else "warn"
            out.append(make_finding(
                rule="Q006",
                severity=sev,
                file=filename, line=1,
                message=f"maintainability index {mi:.1f} (rank {rank}) — "
                        "split or refactor",
                evidence=f"MI={mi:.1f}",
            ))
        return out


def cyclomatic(root: str) -> list[Finding]:
    """Run `radon cc -j` over ``root``; emit Q005 findings for
    rank ≥ C (complexity > 10). Empty list when radon missing."""
    return _RadonCCAnalyzer().run(root)


def maintainability(root: str) -> list[Finding]:
    """Run `radon mi -j` over ``root``; emit Q006 findings for low MI."""
    return _RadonMIAnalyzer().run(root)
