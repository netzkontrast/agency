"""Acceptance — Spec 327: typed Intent + Capability core (the four-concept
interweave's load-bearing slice).

Behaviour under test (observable graph + typed-projection state):
  - core entities (Intent/Invocation/Agent) mirror one-way into typed tables
    keyed by the graph node id;
  - every Invocation maps to the Intent it serves (serves_intent_id NOT NULL,
    resolves) and names its Agent (agent_id) — the directive's invariant;
  - the FK columns track the SERVES / PERFORMED_BY / PARENT_INTENT edges;
  - the projection is one-way + failure-isolated (a mirror error never fails the
    authoritative graph write);
  - enums are enforced from the ontology (rule 2).
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine

from conftest import invoke

scenarios("features/typed_entities.feature")


# ── fixtures / shared state ───────────────────────────────────────────────────

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


# ── helpers ───────────────────────────────────────────────────────────────────

def _store(engine):
    return engine.memory.entities


# ── when ──────────────────────────────────────────────────────────────────────

@when("I capture and confirm an intent and invoke a capability that serves it")
def _capture_confirm_invoke(engine, ctx):
    iid = engine.intent.capture("typed", "typed projection", "rows mirrored")
    engine.intent.confirm(iid)
    _res, inv = invoke(engine, iid, "reflect", "note",
                       scope="observation", text="probe")
    ctx["iid"], ctx["inv"] = iid, inv


@when("I capture an intent and invoke a capability performed by an agent")
def _invoke_with_agent(engine, ctx):
    iid = engine.intent.capture("typed", "agent fk", "agent resolves")
    engine.intent.confirm(iid)
    aid = engine.memory.record("Agent", {"runtime": "external"})
    inv = engine.memory.record("Invocation",
                               {"capability": "x", "verb": "y", "role": "act"})
    engine.memory.link(inv, iid, "SERVES")
    engine.memory.link(inv, aid, "PERFORMED_BY")
    ctx["iid"], ctx["inv"], ctx["aid"] = iid, inv, aid


@when("I capture a child intent under a parent intent")
def _capture_child(engine, ctx):
    parent = engine.intent.capture("parent", "parent deliverable", "parent done")
    child = engine.intent.capture("child", "child deliverable", "child done",
                                  parent_intent_id=parent)
    ctx["parent"], ctx["child"] = parent, child


@when("a typed-projection write fails while recording an intent")
def _force_mirror_failure(engine, ctx, monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("forced typed-projection failure")
    monkeypatch.setattr(_store(engine), "upsert_typed", _boom)
    ctx["iid"] = engine.intent.capture("resilient", "graph wins", "node survives")


@when("I record an intent with an owner that is not in the ontology")
def _bad_owner(engine, ctx):
    try:
        engine.memory.record("Intent", {
            "purpose": "p", "deliverable": "d", "acceptance": "a",
            "status": "draft", "owner": "not-a-real-owner"})
        ctx["rejected"] = False
    except ValueError:
        ctx["rejected"] = True


# ── then ──────────────────────────────────────────────────────────────────────

@then("the intent has a typed Intent row with the same id")
def _intent_row(engine, ctx):
    row = _store(engine).typed_row("Intent", ctx["iid"])
    assert row is not None and row["id"] == ctx["iid"]


@then("the invocation has a typed Invocation row with the same id")
def _inv_row(engine, ctx):
    row = _store(engine).typed_row("Invocation", ctx["inv"])
    assert row is not None and row["id"] == ctx["inv"]


@then("no typed Invocation row has a null serves_intent_id")
def _no_null_serves(engine, ctx):
    rows = _store(engine).typed_rows("Invocation")
    assert rows, "expected at least one Invocation row"
    assert all(r["serves_intent_id"] is not None for r in rows)


@then("every typed Invocation serves_intent_id resolves to a typed Intent row")
def _serves_resolves(engine, ctx):
    rows = _store(engine).typed_rows("Invocation")
    for r in rows:
        assert _store(engine).typed_row("Intent", r["serves_intent_id"]) is not None


@then("the invocation's serves_intent_id equals the target of its SERVES edge")
def _serves_tracks_edge(engine, ctx):
    edge_targets = engine.memory.g.query(
        "MATCH (n)-[:SERVES]->(t) WHERE n.id = $i RETURN t.id AS tid",
        {"i": ctx["inv"]})
    targets = {r["tid"] for r in edge_targets}
    row = _store(engine).typed_row("Invocation", ctx["inv"])
    assert row["serves_intent_id"] in targets


@then("the invocation's agent_id resolves to a typed Agent row")
def _agent_fk(engine, ctx):
    row = _store(engine).typed_row("Invocation", ctx["inv"])
    assert row["agent_id"] == ctx["aid"]
    assert _store(engine).typed_row("Agent", ctx["aid"]) is not None


@then("the child Intent row's parent_intent_id equals the parent id")
def _parent_fk(engine, ctx):
    row = _store(engine).typed_row("Intent", ctx["child"])
    assert row["parent_intent_id"] == ctx["parent"]


@then("the authoritative graph still has the intent node")
def _graph_survives(engine, ctx):
    assert engine.memory.recall(ctx["iid"]) is not None


@then("the record is rejected")
def _rejected(ctx):
    assert ctx["rejected"] is True
