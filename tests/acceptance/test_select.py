"""Acceptance — select capability (Spec 296)."""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, then, when

from conftest import invoke

scenarios("features/select.feature")


def _s(engine, intent, verb, **kw):
    r, _ = invoke(engine, intent, "select", verb, agent_id="agent:test", **kw)
    return r


@when("I list the select archetypes", target_fixture="arch")
def _arch(engine, confirmed_intent):
    return _s(engine, confirmed_intent, "archetypes")


@then("the archetypes include semantic, pattern, and native")
def _arch_three(arch):
    assert {"semantic", "pattern", "native"} <= set(arch["archetypes"])


@when(parsers.parse('I route the operation "{op}" over {n:d} files'), target_fixture="routed")
def _route_files(engine, confirmed_intent, op, n):
    return _s(engine, confirmed_intent, "route", operation=op, file_count=n)


@when(parsers.parse('I route the speed-critical operation "{op}"'), target_fixture="routed")
def _route_speed(engine, confirmed_intent, op):
    return _s(engine, confirmed_intent, "route", operation=op, speed_priority=True)


@when(parsers.parse('I route the operation "{op}"'), target_fixture="routed")
def _route(engine, confirmed_intent, op):
    return _s(engine, confirmed_intent, "route", operation=op)


@then(parsers.parse('the selected approach is "{approach}"'))
def _approach(routed, approach):
    assert routed["approach"] == approach, routed


@then("the selection records a Selection node serving the intent")
def _records(engine, confirmed_intent, routed):
    node = engine.memory.recall_typed(routed["selection_id"], "Selection")
    assert node is not None and node["approach"] == routed["approach"]
    assert engine.memory.has_edge(routed["selection_id"], confirmed_intent, "SERVES")


@then("the selection rationale mentions a direct mapping")
def _rationale(routed):
    assert "direct mapping" in routed["rationale"], routed
