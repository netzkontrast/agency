"""Spec 026 Part B — intent.suggests: the intent→skill projection (Matcher taxonomy)."""
import tempfile

import pytest

from agency.capability import CapabilityBase, verb
from agency.engine import Engine
from agency.ontology import OntologyExtension


class _DeciderCap(CapabilityBase):
    """A test capability whose skill applies via a verb_code Matcher (decider verb)."""
    name = "decider"
    home = "capability"
    ontology = OntologyExtension(skills={"decider-skill": {
        "name": "decider-skill", "kind": "discipline",
        "phases": [{"index": 1, "name": "go", "produces": ["x"]}],
        "applies_when": {"kind": "verb_code",
                         "verb_code": {"capability": "decider", "verb": "decide"}}}})

    @verb(role="transform")
    def decide(self) -> dict:
        return {"matches": True, "confidence": 0.95}


def _mk(extra=None):
    return Engine(tempfile.mktemp(suffix=".db"),
                  extra_capabilities=extra or [], _require_skill_doc=False)


@pytest.fixture
def engine():
    e = _mk()
    try:
        yield e
    finally:
        e.memory.close()


@pytest.fixture
def decider_engine():
    e = _mk([_DeciderCap.as_capability()])
    try:
        yield e
    finally:
        e.memory.close()


def _iid(e):
    # neutral intent text (no skill-words) so `called_state` drives the projection
    i = e.intent.capture("task alpha", "produce output beta", "acceptance gamma")
    e.intent.confirm(i)
    return i


def _call(e, iid, cap, verb, **kw):
    res, _ = e.registry.invoke(e.memory, iid, cap, verb, **kw)
    return res["result"] if isinstance(res, dict) and "result" in res else res


def test_pattern_matcher_projects_to_a_skill(engine):
    iid = _iid(engine)
    out = _call(engine, iid, "intent", "suggests", called_state="which skill should I walk")
    assert out["skill"] == "skills-triage" and out["mode"] == "pattern"
    assert out["confidence"] == 0.8


def test_floor_filters_low_confidence(engine):
    iid = _iid(engine)
    out = _call(engine, iid, "intent", "suggests",
                called_state="which skill should I walk", floor=0.9)
    assert out["skill"] is None and "floor" in out["reason"]


def test_no_matcher_matches_returns_none(engine):
    iid = _iid(engine)
    out = _call(engine, iid, "intent", "suggests", called_state="totally unrelated xyzzy")
    assert out["skill"] is None


def test_verb_code_matcher_invokes_a_decider(decider_engine):
    iid = _iid(decider_engine)
    out = _call(decider_engine, iid, "intent", "suggests", called_state="unrelated xyzzy")
    assert out["skill"] == "decider-skill" and out["mode"] == "verb_code"
    assert out["confidence"] == 0.95


def test_cycle_check_skips_the_verb_in_flight(decider_engine):
    iid = _iid(decider_engine)
    out = _call(decider_engine, iid, "intent", "suggests",
                called_capability="decider", called_verb="decide", called_state="unrelated xyzzy")
    assert out["skill"] != "decider-skill"     # the decider in flight is cycle-skipped
