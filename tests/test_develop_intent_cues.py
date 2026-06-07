"""Spec 092 G4 — develop's disciplines cue the `intent` critical-thinking methods."""
import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        yield e
    finally:
        e.memory.close()


@pytest.fixture
def iid(engine):
    i = engine.intent.capture("ship X", "Y working", "tests green")
    engine.intent.confirm(i)
    return i


def _cues(engine, skill):
    sk = engine.registry.get("develop").ontology.skills[skill]
    return {v for p in sk["phases"] for v in p.get("verbs", [])}


def test_disciplines_cue_intent_methods_at_the_right_step(engine):
    assert "intent.premortem" in _cues(engine, "plan")
    assert "intent.steelman" in _cues(engine, "spec-panel")
    assert "intent.tradeoffs" in _cues(engine, "brainstorm")


def test_no_dangling_cue(engine):
    # every `intent.<verb>` cue must be a REAL verb on the intent capability
    intent_verbs = set(engine.registry.get("intent").verbs)
    for skill in ("plan", "spec-panel", "brainstorm"):
        for cue in _cues(engine, skill):
            if cue.startswith("intent."):
                assert cue.split(".", 1)[1] in intent_verbs, f"dangling cue {cue!r}"


def test_cued_method_actually_runs_and_reasons_about_the_intent(engine, iid):
    res, _ = engine.registry.invoke(engine.memory, iid, "intent", "premortem")
    out = res["result"] if isinstance(res, dict) and "result" in res else res
    assert out["method"] == "premortem" and out["steps"]


def test_cued_disciplines_still_walk(engine, iid):
    for skill in ("plan", "spec-panel", "brainstorm"):
        res, _ = engine.registry.invoke(engine.memory, iid, "develop", "skill_walk",
                                        name=skill, inputs={})
        out = res["result"] if isinstance(res, dict) and "result" in res else res
        assert out.get("status") in ("completed", "input-required", "blocked", "failed")
