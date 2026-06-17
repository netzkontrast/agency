"""Acceptance — recommend capability (Spec 298)."""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, then, when

from conftest import invoke

scenarios("features/recommend.feature")


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
