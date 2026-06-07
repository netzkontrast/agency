"""The `intent` capability — critical-thinking methods that reason about the goal."""
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
    i = engine.intent.capture("ship feature X", "a working auth flow", "tests pass")
    engine.intent.confirm(i)
    return i


def _call(e, iid, cap, verb, **kw):
    res, _ = e.registry.invoke(e.memory, iid, cap, verb, **kw)
    return res["result"] if isinstance(res, dict) and "result" in res else res


_METHODS = ("decompose", "assumptions", "premortem", "first_principles",
            "inversion", "steelman", "second_order", "tradeoffs")


def test_intent_registers_with_critical_thinking_methods(engine):
    cap = engine.registry.get("intent")
    for v in _METHODS:
        assert v in cap.verbs, f"missing method {v}"


def test_methods_default_subject_to_the_serving_intent(engine, iid):
    out = _call(engine, iid, "intent", "premortem")
    assert out["method"] == "premortem"
    assert "a working auth flow" in out["subject"]      # the intent's deliverable
    assert len(out["steps"]) >= 3


def test_explicit_subject_overrides_the_ambient_intent(engine, iid):
    out = _call(engine, iid, "intent", "decompose", subject="migrate the database")
    assert out["subject"] == "migrate the database"


def test_tradeoffs_parses_options_and_criteria(engine, iid):
    out = _call(engine, iid, "intent", "tradeoffs", options="postgres, sqlite", criteria="cost, risk")
    assert out["options"] == ["postgres", "sqlite"]
    assert out["criteria"] == ["cost", "risk"]


def test_tradeoffs_supplies_default_criteria(engine, iid):
    out = _call(engine, iid, "intent", "tradeoffs")
    assert "cost" in out["criteria"] and "reversibility" in out["criteria"]


def test_authored_critical_thinking_discipline_overrides_and_walks(engine, iid):
    cap = engine.registry.get("intent")
    assert "critical-thinking" in cap.ontology.skills        # authored
    assert "intent-usage" not in cap.ontology.skills         # overrides the derived scaffold
    assert _call(engine, iid, "skills", "lint", skill_name="critical-thinking")["ok"] is True
    res, _ = engine.registry.invoke(engine.memory, iid, "develop", "skill_walk",
                                    name="critical-thinking", inputs={})
    out = res["result"] if isinstance(res, dict) and "result" in res else res
    assert out.get("status") in ("completed", "input-required", "blocked", "failed")


def test_suggests_projects_to_critical_thinking(engine, iid):
    out = _call(engine, iid, "intent", "suggests",
                called_state="this decision is risky and the approach is unclear")
    assert out["skill"] == "critical-thinking" and out["mode"] == "pattern"
