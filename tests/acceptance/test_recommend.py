"""Acceptance — recommend capability (Spec 298)."""
from __future__ import annotations

from pytest_bdd import given, parsers, scenarios, then, when

from conftest import invoke

scenarios("features/recommend.feature")


@given(parsers.parse('the "{cap}" capability has been invoked twice'))
def _invoke_twice(engine, confirmed_intent, cap):
    # Two read-only invocations record two Invocation nodes for this capability,
    # giving it a graph usage frequency the router can read back.
    invoke(engine, confirmed_intent, cap, "open_intents", agent_id="agent:test")
    invoke(engine, confirmed_intent, cap, "open_intents", agent_id="agent:test")


@then("the manage recommendation carries a usage count of at least two")
def _manage_usage(rec):
    row = next((r for r in rec["recommendations"] if r["capability"] == "manage"), None)
    assert row is not None, rec
    assert row.get("usage", 0) >= 2, rec


@when(parsers.parse('I ask for a recommendation for "{request}"'), target_fixture="rec")
def _route(engine, confirmed_intent, request):
    r, _ = invoke(engine, confirmed_intent, "recommend", "route",
                  agent_id="agent:test", request=request)
    return r


@then(parsers.parse('a recommendation names the "{cap}" capability'))
def _names(rec, cap):
    caps = {r["capability"] for r in rec["recommendations"]}
    assert cap in caps, rec
    assert all(r["verb"] for r in rec["recommendations"])


@then("the recommendation records a Recommendation node serving the intent")
def _records(engine, confirmed_intent, rec):
    rows = engine.memory.nodes_serving(confirmed_intent, "Recommendation")
    assert rows, "no Recommendation node serving the intent"


# Spec 301 Slice 2 — the walkable discipline (superpowers pattern).
@when(parsers.parse('I walk the "{name}" discipline to its gate'), target_fixture="walk")
def _walk(engine, confirmed_intent, name):
    r, _ = invoke(engine, confirmed_intent, "develop", "skill_walk",
                  agent_id="agent:test", name=name,
                  inputs={"request": "lint a skill",
                          "recommendations": [{"capability": "plugin"}],
                          "chosen": "plugin", "rationale": "fits the goal"})
    return r


@then("the discipline pauses at a hard gate")
def _gate(walk):
    assert walk.get("status") == "input-required", walk
