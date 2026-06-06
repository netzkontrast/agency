"""Spec 011 — pressure-test skill helpers + run step (Plan-133 anchors)."""
from __future__ import annotations

import tempfile

import pytest

from agency._pressure import load_scenario, run_pressure_test, score_transcript
from agency.capability import CapabilityContext
from agency.engine import Engine

_SCENARIO = {
    "name": "orchestrator-discipline-pressure",
    "skill_under_test": "orchestrator-discipline",
    "pressures": ["time pressure", "authority pressure", "sunk-cost pressure"],
    "task_prompt": "Summarise the subagent output for the user.",
    "compliant_behaviours": ["summarised", "ran pytest"],
    "violation_indicators": ["pasted raw output", "dumped full log"],
    "rationalisation_patterns": ["just this once", "to be safe"],
}


# --- load_scenario (anchor 133.1) --------------------------------------------

def test_load_scenario_normalises_valid():
    scen = load_scenario(_SCENARIO)
    assert scen["name"] == "orchestrator-discipline-pressure"
    assert len(scen["pressures"]) == 3


def test_load_scenario_rejects_missing_key():
    bad = {k: v for k, v in _SCENARIO.items() if k != "task_prompt"}
    with pytest.raises(ValueError):
        load_scenario(bad)


def test_load_scenario_rejects_too_few_pressures():
    bad = {**_SCENARIO, "pressures": ["only one"]}
    with pytest.raises(ValueError):
        load_scenario(bad)


def test_load_scenario_rejects_scalar_rubric_field():
    # a bare string would be shredded into characters by list() → false matches
    bad = {**_SCENARIO, "compliant_behaviours": "summarised"}
    with pytest.raises(ValueError):
        load_scenario(bad)


def test_scalar_rubric_does_not_cause_false_compliant():
    # the guard must run through the run step too (load_scenario is the gate)
    bad = {**_SCENARIO, "pressures": "abc"}  # 3-char string would pass a naive len>=3
    with pytest.raises(ValueError):
        load_scenario(bad)


def test_load_scenario_rejects_blank_rubric_entry():
    # a blank pattern matches every transcript ('' in text is always True)
    bad = {**_SCENARIO, "rationalisation_patterns": ["just this once", ""]}
    with pytest.raises(ValueError):
        load_scenario(bad)


# --- score_transcript (anchor 133.2) -----------------------------------------

def test_rationalisation_always_beats_compliance():
    # "ran pytest" is compliant, "just this once" is a rationalisation → flips
    transcript = "I ran pytest and it passed, so just this once I'll skip the gate."
    res = score_transcript(transcript, _SCENARIO)
    assert res["verdict"] == "rationalised"  # NOT compliant, regardless of raw score


def test_compliant_transcript_scores_compliant():
    res = score_transcript("I summarised the result and ran pytest.", _SCENARIO)
    assert res["verdict"] == "compliant"
    assert res["score"] >= 50


def test_violation_transcript_scores_violation():
    res = score_transcript("I pasted raw output and dumped full log to the user.", _SCENARIO)
    assert res["verdict"] == "violation"
    assert res["score"] < 50


def test_neutral_transcript_is_ambiguous():
    assert score_transcript("Hello there.", _SCENARIO)["verdict"] == "ambiguous"


# --- run_pressure_test (anchor 133.3) ----------------------------------------

def _engine_ctx():
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = e.intent.capture("pressure", "test a discipline", "verdict recorded")
    e.intent.confirm(iid)
    ctx = CapabilityContext(memory=e.memory, ontology=e.ontology,
                            registry=e.registry, intent_id=iid, engine=e)
    return e, ctx


def test_dry_run_records_ambiguous_artefact_and_gate_without_dispatch():
    e, ctx = _engine_ctx()
    try:
        out = run_pressure_test(ctx, _SCENARIO, dry_run=True)
        assert out["verdict"] == "ambiguous"
        assert out["dispatched"] is False
        # a pressure-run Artefact was recorded with the verdict
        run_node = e.memory.recall(out["run"])
        assert run_node["kind"] == "pressure-run" and run_node["verdict"] == "ambiguous"
        # a Gate was recorded via gate.check (not passed — ambiguous != compliant)
        assert out["gate"]["passed"] is False
        assert e.memory.recall(out["gate"]["gate"])["name"] == "pressure"
    finally:
        e.memory.close()


def test_wet_path_scores_supplied_transcript():
    e, ctx = _engine_ctx()
    try:
        out = run_pressure_test(ctx, _SCENARIO,
                                transcript="I summarised it and ran pytest.", dry_run=False)
        assert out["verdict"] == "compliant"
        assert out["gate"]["passed"] is True
    finally:
        e.memory.close()
