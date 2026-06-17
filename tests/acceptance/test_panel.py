"""Acceptance — panel capability (Spec 294)."""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, then, when

from conftest import invoke

scenarios("features/panel.feature")


def _p(engine, intent, verb, **kw):
    r, _ = invoke(engine, intent, "panel", verb, agent_id="agent:test", **kw)
    return r


@when("I list the panel experts", target_fixture="roster")
def _experts(engine, confirmed_intent):
    return _p(engine, confirmed_intent, "experts")


@then("the roster has nine experts including Porter and Taleb")
def _roster_nine(roster):
    assert roster["count"] == 9
    names = {e["name"] for e in roster["experts"]}
    assert {"Porter", "Taleb"} <= names and all(e["framework"] for e in roster["experts"])


@when(parsers.parse('I convene the panel on "{subject}"'), target_fixture="panel")
def _convene(engine, confirmed_intent, subject):
    return _p(engine, confirmed_intent, "convene", subject=subject)


@when(parsers.parse('I convene the full panel on "{subject}"'), target_fixture="panel")
def _convene_full(engine, confirmed_intent, subject):
    return _p(engine, confirmed_intent, "convene", subject=subject, focus="full")


@then(parsers.parse('the panel mode is "{mode}"'))
def _mode(panel, mode):
    assert panel["mode"] == mode, panel


@then("the panel records a Panel node serving the intent")
def _records(engine, confirmed_intent, panel):
    node = engine.memory.recall_typed(panel["panel_id"], "Panel")
    assert node is not None and node["mode"] == panel["mode"]
    assert engine.memory.has_edge(panel["panel_id"], confirmed_intent, "SERVES")


@then("each expert contributes a question")
def _questions(panel):
    assert panel["analysis"] and all("question" in a for a in panel["analysis"])


@then("each expert contributes a framework prompt")
def _prompts(panel):
    assert panel["analysis"] and all("prompt" in a for a in panel["analysis"])


@then("the panel includes all nine experts")
def _all_nine(panel):
    assert len(panel["experts"]) == 9


@when(parsers.parse('I walk the "{name}" discipline to its gate'), target_fixture="walk")
def _walk(engine, confirmed_intent, name):
    r, _ = invoke(engine, confirmed_intent, "develop", "skill_walk",
                  agent_id="agent:test", name=name,
                  inputs={"subject": "x", "mode": "debate", "experts": ["Porter"],
                          "analysis": [{"a": 1}], "tensions": ["a vs b"],
                          "synthesis": "done"})
    return r


@then("the discipline pauses at a hard gate")
def _gate(walk):
    assert walk.get("status") == "input-required", walk
