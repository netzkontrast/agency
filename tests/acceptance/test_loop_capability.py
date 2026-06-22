"""Acceptance — the loop capability (Spec 387 W1): reachable + provenance-recording.

The dormant-surface audit as a STANDING test: the looper port's verbs are on the
wire surface, schema'd, and record an `Invocation` when invoked — the moat the
bare spine functions (363-369) bypassed. This scenario set would have FAILED on
the spine-only port (no `loop` capability, no `Invocation{capability:"loop"}`).
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, then, when

from conftest import call_tool, invoke, tool_names

scenarios("features/loop_capability.feature")


@when("I invoke the loop frame_goal verb through the registry", target_fixture="box")
def _invoke_frame(engine, confirmed_intent):
    result, inv_id = invoke(
        engine, confirmed_intent, "loop", "frame_goal",
        statement="Map ACME onboarding into an agent workflow",
        definition_of_done="A LOOP.md, every step mapped to a tool or human, nothing TBD")
    return {"result": result, "inv_id": inv_id, "intent": confirmed_intent}


@when(parsers.parse('I search the live registry for "{query}"'), target_fixture="box")
def _search(engine, query):
    # search/get_schema are the codemode 3-verb contract surface.
    return {"search": call_tool(engine, "search", {"query": query}, codemode=True)}


@then("the wire surface exposes the loop verbs frame_goal, open, advance, compile, emit")
def _wire_surface(engine):
    names = tool_names(engine, codemode=False)
    for verb in ("frame_goal", "open", "advance", "compile", "emit"):
        assert f"capability_loop_{verb}" in names, \
            (verb, sorted(n for n in names if "loop" in n))


@then("get_schema returns a schema for the loop open verb")
def _schema(engine):
    res = call_tool(engine, "get_schema", {"tools": ["capability_loop_open"]}, codemode=True)
    assert res, res
    blob = str(res)
    assert "loop_open" in blob or "goal_id" in blob, blob


@then("an Invocation with capability loop serves the intent")
def _provenance(engine, box):
    assert box["inv_id"], "no invocation id returned by registry.invoke"
    rows = engine.memory.g.query(
        "MATCH (n:Invocation)-[:SERVES]->(t) WHERE t.id=$iid AND n.capability='loop' RETURN n",
        {"iid": box["intent"]})
    assert rows, "no loop Invocation serves the intent (the provenance moat is still bypassed)"


@then("the goal is framed as an Intent")
def _goal_framed(engine, box):
    gid = box["result"].get("goal_id")
    assert gid, box["result"]
    assert engine.memory.recall_typed(gid, "Intent") is not None, "goal_id is not an Intent"


@then("a loop verb is among the results")
def _search_loop(box):
    assert "loop" in str(box["search"]).lower(), box["search"]
