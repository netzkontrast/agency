"""Acceptance — persona capability (Spec 297)."""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, then, when

from conftest import invoke

scenarios("features/persona.feature")


def _p(engine, intent, verb, **kw):
    r, _ = invoke(engine, intent, "persona", verb, agent_id="agent:test", **kw)
    return r


@when("I list the personas", target_fixture="roster")
def _list(engine, confirmed_intent):
    return _p(engine, confirmed_intent, "list")


@then("the persona roster includes security-engineer and refactoring-expert")
def _roster(roster):
    names = {p["name"] for p in roster["personas"]}
    assert {"security-engineer", "refactoring-expert"} <= names
    assert all(p["focus"] and p["approach"] for p in roster["personas"])


@when(parsers.parse('I recommend a persona for "{task}"'), target_fixture="rec")
def _recommend(engine, confirmed_intent, task):
    return _p(engine, confirmed_intent, "recommend", task=task)


@then(parsers.parse('the top recommended persona is "{name}"'))
def _top(rec, name):
    assert rec["top"] == name, rec


@when(parsers.parse('I summon the auto persona for "{task}"'), target_fixture="summoned")
def _summon_auto(engine, confirmed_intent, task):
    return _p(engine, confirmed_intent, "summon", persona="auto", task=task)


@when(parsers.parse('I summon the "{persona}" persona for "{task}"'), target_fixture="summoned")
def _summon_named(engine, confirmed_intent, persona, task):
    return _p(engine, confirmed_intent, "summon", persona=persona, task=task)


@then(parsers.parse('the summoned persona is "{name}"'))
def _summoned_name(summoned, name):
    assert summoned["persona"] == name, summoned


@then("the brief embeds the role focus and the task")
def _brief(summoned):
    b = summoned["brief"]
    assert "Role — performance-engineer" in b and "optimize throughput" in b


@then("summon records a PersonaBrief node serving the intent")
def _records(engine, confirmed_intent, summoned):
    node = engine.memory.recall_typed(summoned["persona_brief_id"], "PersonaBrief")
    assert node is not None and node["persona"] == summoned["persona"]
    assert engine.memory.has_edge(summoned["persona_brief_id"], confirmed_intent, "SERVES")
