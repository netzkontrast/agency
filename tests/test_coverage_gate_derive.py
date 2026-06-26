"""Spec 169 Slice 2 — the live coverage-gate deriver invariants.

`derive_gate_results` turns the live registry's test-gap report (Spec 054) into
one typed `GateResult` per capability — the fully-derivable verb-test-coverage
dimension of the CI gate. A new capability without a test fails its GateResult.
"""
from __future__ import annotations

from agency._coverage_gate import (GateResult, derive_gate_results,
                                    gate_summary)
from agency.engine import Engine
from agency.toolresult import Codes


def test_gate_infra_error_code_exists():
    assert Codes.GATE_INFRA_ERROR == "gate_infra_error"


def test_one_gate_result_per_live_capability():
    e = Engine(":memory:")
    try:
        results = derive_gate_results(e)
        assert all(isinstance(r, GateResult) for r in results)
        names = {r.capability for r in results}
        live = {n for n in e.registry.names() if not n.startswith("_")}
        assert names == live
    finally:
        e.memory.close()


def test_verdict_keys_off_the_live_test_gap_report():
    e = Engine(":memory:")
    try:
        untested = set(e._drift_signals().get("capabilities_without_tests", []))
        results = {r.capability: r for r in derive_gate_results(e)}
        # relationship: a capability fails iff it is in the live test-gap set
        for name, r in results.items():
            assert (r.verdict == "fail") == (name in untested)
            if r.verdict == "fail":
                assert name in r.missing_tests
    finally:
        e.memory.close()


def test_gate_summary_ready_iff_no_failing_capabilities():
    e = Engine(":memory:")
    try:
        summ = gate_summary(e)
        assert summ["ready"] == (not summ["failing"])
        assert summ["passing"] + len(summ["failing"]) == summ["capabilities"]
    finally:
        e.memory.close()
