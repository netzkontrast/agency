"""Spec 169 Slice 1 — typed GateResult + pure evaluate() for the CI gate.

The CI gate has three concerns: coverage trend (non-decreasing per
capability), flake count (zero tolerance), and verb-test coverage (every
verb has a test). Slice 1 unifies these in one typed result so the CI
step can branch on `verdict` rather than parsing free text.

Slice 2 wires evaluate() into the actual CI workflow + tracks the
baseline in `Plan/_planning/coverage-baseline.json` (Spec 054 drift
pattern). Today's surface is the pure shape + invariants offline-clean.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Verdict = Literal["pass", "fail"]
_VALID_VERDICTS = ("pass", "fail")
DEFAULT_EPSILON = 0.005   # 0.5% flutter allowance


@dataclass(frozen=True)
class GateResult:
    """Typed result of the CI gate for ONE capability.

    `delta = current_coverage - baseline_coverage` (signed).
    `verdict='fail'` iff (coverage drops past epsilon) OR (any flake) OR
    (any verb without a test). Slice 1 enforces the data invariants at
    construction; the evaluate() helper computes the verdict + delta."""

    capability:         str
    baseline_coverage:  float
    current_coverage:   float
    delta:              float
    flake_count:        int
    missing_tests:      tuple[str, ...]
    verdict:            Verdict

    def __post_init__(self) -> None:
        if not isinstance(self.capability, str) or not self.capability:
            raise ValueError(
                f"capability must be a non-empty string; got {self.capability!r}")
        if self.verdict not in _VALID_VERDICTS:
            raise ValueError(
                f"verdict must be one of {_VALID_VERDICTS}; got {self.verdict!r}")
        for label, val in (("baseline_coverage", self.baseline_coverage),
                            ("current_coverage", self.current_coverage)):
            if not (0.0 <= val <= 1.0):
                raise ValueError(
                    f"{label} must be in [0.0, 1.0]; got {val}")
        if self.flake_count < 0:
            raise ValueError(
                f"flake_count must be >= 0; got {self.flake_count}")


def evaluate(*, capability: str, baseline: float, current: float,
              missing: tuple[str, ...] = (), flakes: int = 0,
              epsilon: float = DEFAULT_EPSILON) -> GateResult:
    """Compute the typed GateResult for one capability.

    Verdict rules:
      - fail when `current < baseline - epsilon` (regression past flutter)
      - fail when `flakes > 0` (zero tolerance)
      - fail when `missing` is non-empty (every verb needs a test)
      - else pass (incl. bootstrap: baseline=0 + current>0)
    """
    delta = round(current - baseline, 6)
    failed = (
        (current < (baseline - epsilon)) or
        (flakes > 0) or
        (len(missing) > 0)
    )
    return GateResult(
        capability=capability,
        baseline_coverage=baseline,
        current_coverage=current,
        delta=delta,
        flake_count=flakes,
        missing_tests=tuple(missing),
        verdict="fail" if failed else "pass",
    )
