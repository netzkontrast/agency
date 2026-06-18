"""Acceptance — mode capability (Spec 295)."""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, then, when

from conftest import invoke

scenarios("features/mode.feature")


def _m(engine, intent, verb, **kw):
    r, _ = invoke(engine, intent, "mode", verb, agent_id="agent:test", **kw)
    return r


@when("I list the modes", target_fixture="roster")
def _list(engine, confirmed_intent):
    return _m(engine, confirmed_intent, "list")


@then("the mode roster has five modes including brainstorming and introspection")
def _roster(roster):
    assert roster["count"] == 5
    names = {m["name"] for m in roster["modes"]}
    assert {"brainstorming", "introspection"} <= names
    assert all(m["behaviors"] for m in roster["modes"])


@when(parsers.parse('I detect the mode for "{context}"'), target_fixture="detect_result")
def _detect(engine, confirmed_intent, context):
    return _m(engine, confirmed_intent, "detect", context=context)


@then(parsers.parse('the top detected mode is "{mode}"'))
def _top(detect_result, mode):
    assert detect_result["top"] == mode, detect_result


@when(parsers.parse('I activate the auto mode for "{context}"'), target_fixture="activation")
def _activate(engine, confirmed_intent, context):
    return _m(engine, confirmed_intent, "activate", mode="auto", context=context)


@then(parsers.parse('the activated mode is "{mode}"'))
def _activated(activation, mode):
    assert activation["mode"] == mode, activation


@then("activation records a ModeActivation node serving the intent")
def _records(engine, confirmed_intent, activation):
    node = engine.memory.recall_typed(activation["activation_id"], "ModeActivation")
    assert node is not None and node["mode"] == activation["mode"]
    assert engine.memory.has_edge(activation["activation_id"], confirmed_intent, "SERVES")


@then("the activated mode returns behavioral rules")
def _rules(activation):
    assert activation["behaviors"] and isinstance(activation["behaviors"], list)


# Spec 301 Slice 2 — the walkable discipline (superpowers pattern).
@when(parsers.parse('I walk the "{name}" discipline to its gate'), target_fixture="walk")
def _walk(engine, confirmed_intent, name):
    r, _ = invoke(engine, confirmed_intent, "develop", "skill_walk",
                  agent_id="agent:test", name=name,
                  inputs={"context": "exploring options",
                          "candidate_modes": ["brainstorming"],
                          "active_mode": "brainstorming",
                          "rationale": "fits the goal"})
    return r


@then("the discipline pauses at a hard gate")
def _gate(walk):
    assert walk.get("status") == "input-required", walk
