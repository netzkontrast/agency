"""Spec 169 Slice 1 — typed GateResult + verdict invariants."""
from __future__ import annotations

import pytest

from agency._coverage_gate import GateResult, evaluate


def test_gate_result_typed_shape():
    r = GateResult(
        capability="analyze", baseline_coverage=0.85,
        current_coverage=0.88, delta=0.03,
        flake_count=0, missing_tests=(), verdict="pass",
    )
    assert r.capability == "analyze"
    assert r.verdict == "pass"


def test_evaluate_pass_when_coverage_grows_no_flakes_no_missing():
    r = evaluate(capability="x", baseline=0.7, current=0.8,
                  missing=(), flakes=0)
    assert r.verdict == "pass"
    assert r.delta == pytest.approx(0.10)
    assert r.flake_count == 0


def test_evaluate_fail_when_coverage_drops_past_epsilon():
    """`current < baseline - epsilon` → fail."""
    r = evaluate(capability="x", baseline=0.9, current=0.6,
                  missing=(), flakes=0)
    assert r.verdict == "fail"
    assert r.delta < 0


def test_evaluate_pass_when_coverage_drops_within_epsilon():
    """Tiny coverage dip (≤ epsilon) is treated as flutter, not regression."""
    r = evaluate(capability="x", baseline=0.85, current=0.849,
                  missing=(), flakes=0, epsilon=0.005)
    assert r.verdict == "pass"


def test_evaluate_fail_on_any_flake():
    """Even with rising coverage, a single flake fails the gate."""
    r = evaluate(capability="x", baseline=0.5, current=0.9,
                  missing=(), flakes=1)
    assert r.verdict == "fail"


def test_evaluate_fail_on_any_missing_test():
    """A capability verb without a test fails the gate."""
    r = evaluate(capability="x", baseline=0.5, current=0.9,
                  missing=("verb:foo",), flakes=0)
    assert r.verdict == "fail"
    assert r.missing_tests == ("verb:foo",)


def test_evaluate_empty_baseline_passes_when_current_positive():
    """Bootstrap case: zero baseline + positive current = pass (the
    capability is graduating from no-tests to some tests)."""
    r = evaluate(capability="x", baseline=0.0, current=0.3,
                  missing=(), flakes=0)
    assert r.verdict == "pass"


def test_gate_result_rejects_invalid_verdict():
    with pytest.raises(ValueError):
        GateResult(capability="x", baseline_coverage=0.5,
                    current_coverage=0.5, delta=0.0,
                    flake_count=0, missing_tests=(), verdict="bogus")


def test_gate_result_rejects_coverage_out_of_range():
    """Coverage values must be in [0.0, 1.0]."""
    with pytest.raises(ValueError):
        GateResult(capability="x", baseline_coverage=1.5,
                    current_coverage=0.5, delta=-1.0,
                    flake_count=0, missing_tests=(), verdict="pass")
    with pytest.raises(ValueError):
        GateResult(capability="x", baseline_coverage=0.5,
                    current_coverage=-0.1, delta=-0.6,
                    flake_count=0, missing_tests=(), verdict="pass")


def test_gate_result_rejects_empty_capability():
    with pytest.raises(ValueError):
        GateResult(capability="", baseline_coverage=0.5,
                    current_coverage=0.5, delta=0.0,
                    flake_count=0, missing_tests=(), verdict="pass")
