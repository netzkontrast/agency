"""Spec 011 — decidable gate predicates (no new capability/verb).

`spec_validate` and `confidence_check` are pure module helpers (CLUSTERS:18 — a
predicate that blocks a phase IS a `gate`). Their verdict is recorded through the
existing `gate.check` verb, so a failed predicate is real Gate provenance that
pauses the Lifecycle. No new node label, no new verb.
"""
from __future__ import annotations

import tempfile

import pytest

from agency._predicates import confidence_check, spec_validate
from agency.engine import Engine


# --- spec_validate: RFC-2119 + Gherkin classification ------------------------

def test_spec_validate_passes_with_normative_and_gherkin():
    text = (
        "The system MUST persist the graph.\n"
        "Scenario: a node is recorded\n"
        "  Given an engine\n  When record is called\n  Then a node exists\n"
    )
    res = spec_validate(text)
    assert res["ok"] is True
    assert res["findings"] == []


def test_spec_validate_flags_missing_normative_keyword():
    text = "Scenario: x\n  Given a\n  When b\n  Then c\n"  # gherkin but no MUST/SHALL/...
    res = spec_validate(text)
    assert res["ok"] is False
    assert any(f["rule"] == "rfc2119" for f in res["findings"])


def test_spec_validate_flags_missing_gherkin():
    text = "The engine MUST do the thing. It SHOULD also be fast."  # normative, no scenario
    res = spec_validate(text)
    assert res["ok"] is False
    assert any(f["rule"] == "gherkin" for f in res["findings"])


def test_spec_validate_requires_step_under_the_scenario_header():
    # A Scenario header with NO steps, plus an unrelated step in the preamble
    # (before any Scenario), must NOT pass the Gherkin gate.
    text = (
        "Given some stray preamble line that is not under a scenario.\n"
        "The system MUST work.\n"
        "Scenario: empty block with no steps beneath it\n"
    )
    res = spec_validate(text)
    assert res["ok"] is False
    assert any(f["rule"] == "gherkin" for f in res["findings"])


# --- confidence_check: go-threshold predicate --------------------------------

def test_confidence_check_scores_and_blocks_below_threshold():
    res = confidence_check([
        {"claim": "tests pass", "ok": True},
        {"claim": "spec validated", "ok": True},
        {"claim": "no orphans", "ok": False},
        {"claim": "drift clean", "ok": False},
        {"claim": "reviewed", "ok": False},
    ])  # 2/5 = 0.4
    assert res["score"] == pytest.approx(0.4)
    assert set(res["blocking"]) == {"no orphans", "drift clean", "reviewed"}


def test_confidence_check_full_passes_threshold():
    res = confidence_check([{"claim": "a", "ok": True}, {"claim": "b", "ok": True}])
    assert res["score"] == 1.0
    assert res["blocking"] == []


def test_confidence_check_empty_is_not_confident():
    res = confidence_check([])
    assert res["score"] == 0.0 and res["blocking"] == []


# --- the gate facet: sub-threshold confidence blocks the phase as a Gate ------

def test_subthreshold_confidence_records_blocked_gate_and_pauses():
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        iid = e.intent.capture("p", "d", "a")
        e.intent.confirm(iid)
        lc = e.memory.record("Lifecycle", {"state": "working", "phase": 0})
        e.memory.link(lc, iid, "SERVES")

        score = confidence_check([{"claim": "x", "ok": False}, {"claim": "y", "ok": True},
                                  {"claim": "z", "ok": False}])  # 0.33 < 0.9
        res, _ = e.registry.invoke(
            e.memory, iid, "gate", "check",
            lifecycle_id=lc, name="confidence",
            passed=score["score"] >= 0.9, evidence=str(score["blocking"]),
        )
        assert res["result"]["passed"] is False
        # the Lifecycle paused at input-required (BLOCKED_ON gate)
        assert e.memory.recall(lc)["state"] == "input-required"
    finally:
        e.memory.close()
