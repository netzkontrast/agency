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


def derive_gate_results(engine) -> "tuple[GateResult, ...]":
    """Slice 2 — one :class:`GateResult` per capability from the LIVE registry's
    verb-test-coverage check (the fully-derivable invariant: every capability has
    ≥ 1 test file). This is the part of the gate that needs no pytest-cov runtime:
    ``engine._drift_signals()['capabilities_without_tests']`` IS the test-gap report
    (Spec 054), so a new capability without a test fails its GateResult.

    The coverage-% TREND dimension (baseline JSON refreshed per merge) + flake
    re-run + the CI-workflow wiring are deferred Slices 3-5; here baseline ==
    current == 1.0 (tested) / 0.0 (gap), so the verdict keys solely off
    ``missing_tests`` and never makes an un-grounded coverage-% claim.
    """
    untested = set(engine._drift_signals().get("capabilities_without_tests", []))
    results = []
    for name in sorted(engine.registry.names()):
        if name.startswith("_"):
            continue
        gap = name in untested
        # missing carries the capability id when its test file is absent — the
        # derivable verb-test-coverage signal (capability granularity).
        missing = (name,) if gap else ()
        cov = 0.0 if gap else 1.0
        results.append(evaluate(capability=name, baseline=cov, current=cov,
                                missing=missing))
    return tuple(results)


def gate_summary(engine) -> dict:
    """A doctor-friendly roll-up of :func:`derive_gate_results` — the live
    verb-test-coverage gate at a glance. ``ready`` iff every capability passes
    (zero test-gaps)."""
    results = derive_gate_results(engine)
    failing = [r.capability for r in results if r.verdict == "fail"]
    return {"capabilities": len(results),
            "passing": sum(1 for r in results if r.verdict == "pass"),
            "failing": failing,
            "ready": not failing}
