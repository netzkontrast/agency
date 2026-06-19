"""Acceptance — Spec 330: the typed Intent read API (IntentStore) + parity gate.

Behaviour under test:
  - serves / provenance return the same sets as the equivalent Cypher traversal
    (the parity gate — the typed projection never diverges from the graph);
  - intent_tree follows the PARENT_INTENT chain;
  - fulfilment reports the Intent-owned Gate verdict;
  - manage.state consumes the typed fulfilment read (load-bearing, not dormant).
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import scenarios, then, when, given

from agency.engine import Engine

from conftest import invoke

scenarios("features/typed_read_api.feature")


@pytest.fixture
def ctx():
    return {}


@pytest.fixture
def engine():
    eng = Engine(tempfile.mktemp(suffix=".db"))
    yield eng
    eng.memory.close()


@given("a fresh agency engine")
def _fresh(engine):
    return engine


def _intents(engine):
    return engine.memory.intents


# ── when ──────────────────────────────────────────────────────────────────────

@when("an invocation serving an intent produces an artefact serving it")
def _inv_produces(engine, ctx):
    iid = engine.intent.capture("read", "typed read api", "joins not cypher")
    engine.intent.confirm(iid)
    inv = engine.memory.record("Invocation",
                               {"capability": "c", "verb": "v", "role": "act"})
    engine.memory.link(inv, iid, "SERVES")
    art = engine.memory.record("Artefact", {"kind": "report"})
    engine.memory.link(inv, art, "PRODUCES")
    engine.memory.link(art, iid, "SERVES")
    ctx.update(iid=iid, inv=inv, art=art)


@when("I capture a child intent under a parent intent")
def _capture_child(engine, ctx):
    parent = engine.intent.capture("parent", "parent deliverable", "parent done")
    child = engine.intent.capture("child", "child deliverable", "child done",
                                  parent_intent_id=parent)
    ctx.update(parent=parent, child=child)


@when("I capture and confirm an intent")
def _capture_confirm(engine, ctx):
    iid = engine.intent.capture("fulfil", "fulfilment read", "gate verdict")
    engine.intent.confirm(iid)
    ctx["iid"] = iid


# ── then ──────────────────────────────────────────────────────────────────────

@then("IntentStore serves matches the SERVES-Invocation set from the graph")
def _serves_parity(engine, ctx):
    typed = {i["id"] for i in _intents(engine).serves(ctx["iid"])}
    rows = engine.memory.g.query(
        "MATCH (i:Intent)<-[:SERVES]-(x:Invocation) WHERE i.id = $i RETURN x.id AS x",
        {"i": ctx["iid"]})
    graph = {r["x"] for r in rows}
    assert typed == graph and ctx["inv"] in typed


@then("IntentStore provenance invocations match the graph")
def _prov_parity(engine, ctx):
    prov = _intents(engine).provenance(ctx["iid"])
    typed = {i["id"] for i in prov["invocations"]}
    rows = engine.memory.g.query(
        "MATCH (i:Intent)<-[:SERVES]-(x:Invocation) WHERE i.id = $i RETURN x.id AS x",
        {"i": ctx["iid"]})
    assert typed == {r["x"] for r in rows}


@then("IntentStore provenance includes the produced artefact")
def _prov_artefact(engine, ctx):
    prov = _intents(engine).provenance(ctx["iid"])
    assert ctx["art"] in {a["id"] for a in prov["artefacts"]}


@then("IntentStore intent_tree of the parent includes both intents")
def _tree(engine, ctx):
    ids = {i["id"] for i in _intents(engine).intent_tree(ctx["parent"])}
    assert ctx["parent"] in ids and ctx["child"] in ids


@then("IntentStore fulfilment carries a verdict gate for that intent")
def _fulfilment(engine, ctx):
    f = _intents(engine).fulfilment(ctx["iid"])
    assert f["intent_id"] == ctx["iid"]
    assert f["verdict_gate"] is not None
    assert isinstance(f["fulfilled"], bool)


@then("manage state for that intent includes a fulfilment block")
def _manage_state(engine, ctx):
    res, _ = invoke(engine, ctx["iid"], "manage", "state",
                    agent_id="agent:test", for_intent_id=ctx["iid"])
    res = res.get("result", res) if isinstance(res, dict) else res
    assert "fulfilment" in res
    assert res["fulfilment"]["intent_id"] == ctx["iid"]
