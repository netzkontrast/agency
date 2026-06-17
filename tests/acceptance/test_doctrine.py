"""Acceptance — doctrine capability: queryable principles + rules (Spec 303)."""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, then, when

from conftest import invoke

scenarios("features/doctrine.feature")


def _d(engine, intent, verb, **kw):
    r, _ = invoke(engine, intent, "doctrine", verb, agent_id="agent:test", **kw)
    return r


# ── principles ────────────────────────────────────────────────────────────────

@when("I ask doctrine.principles", target_fixture="principles_result")
def _principles(engine, confirmed_intent):
    return _d(engine, confirmed_intent, "principles")


@then(parsers.parse('the principles roster includes "{name}"'))
def _principles_includes(principles_result, name):
    names = {p["name"] for p in principles_result["principles"]}
    assert name in names, principles_result


# ── rules ─────────────────────────────────────────────────────────────────────

@when(parsers.parse('I ask doctrine.rules with priority "{priority}"'),
      target_fixture="rules_result")
def _rules(engine, confirmed_intent, priority):
    return _d(engine, confirmed_intent, "rules", priority=priority)


@then(parsers.parse('every returned rule has priority "{priority}"'))
def _rules_priority(rules_result, priority):
    assert all(r["priority"] == priority for r in rules_result["rules"]), rules_result


@then("at least one critical rule is returned")
def _rules_nonempty(rules_result):
    assert rules_result["count"] >= 1, rules_result


# ── resolve ───────────────────────────────────────────────────────────────────

@when(parsers.parse('I ask doctrine.resolve between "{a}" and "{b}"'),
      target_fixture="resolve_result")
def _resolve(engine, confirmed_intent, a, b):
    return _d(engine, confirmed_intent, "resolve", a=a, b=b)


@then(parsers.parse('resolve names "{winner}" the winner'))
def _resolve_winner(resolve_result, winner):
    assert resolve_result["winner_category"] == winner, resolve_result


# ── cite ──────────────────────────────────────────────────────────────────────

@when(parsers.parse('I cite the "{name}" principle'), target_fixture="cite_result")
def _cite(engine, confirmed_intent, name):
    return _d(engine, confirmed_intent, "cite", name=name)


@then("the citation carries an id")
def _cite_id(cite_result):
    assert cite_result.get("citation_id", "").startswith("doctrinecitation:"), cite_result


@then(parsers.parse('a DoctrineCitation for "{name}" serves the confirmed intent'))
def _cite_serves(engine, confirmed_intent, name):
    rows = engine.memory.g.query(
        "MATCH (c:DoctrineCitation)-[:SERVES]->(t) WHERE t.id = $iid "
        "AND c.name = $n RETURN c",
        {"iid": confirmed_intent, "n": name})
    assert rows, "expected a DoctrineCitation for the principle serving the intent"


@then("the citation result carries an error")
def _cite_error(cite_result):
    assert "error" in cite_result, cite_result


# ── gate adjudication (the real caller — proves doctrine.resolve is not dormant) ─

@when(parsers.parse('I adjudicate a gate between "{a}" and "{b}"'),
      target_fixture="adjudicate_result")
def _adjudicate(engine, confirmed_intent, a, b):
    r, _ = invoke(engine, confirmed_intent, "gate", "adjudicate",
                  agent_id="agent:test", a=a, b=b)
    return r


@then("the gate adjudication names the safety concern the winner")
def _adjudicate_winner(adjudicate_result):
    res = adjudicate_result.get("result", adjudicate_result)
    assert res["winner_category"] == "safety", adjudicate_result


@then("a doctrine.resolve invocation serves the confirmed intent")
def _resolve_invocation_served(engine, confirmed_intent):
    rows = engine.memory.g.query(
        "MATCH (i:Invocation)-[:SERVES]->(t) WHERE t.id = $iid "
        "AND i.capability = 'doctrine' AND i.verb = 'resolve' RETURN i",
        {"iid": confirmed_intent})
    assert rows, "expected a doctrine.resolve Invocation serving the intent"
