"""Acceptance — Spec 329: typed Lifecycle state + the Memory provenance spine.

Behaviour under test:
  - an Artefact's produced_by_id (PRODUCES) + serves_intent_id (SERVES) are typed
    FKs; an Intent-produced artefact (no invocation) keeps produced_by_id null;
  - a LifecycleState weaves to its Intent via serves_intent_id;
  - EVERY live graph edge is mirrored into the typed Edge spine (completeness),
    a new link adds exactly one Edge row, and the spine write is one-way +
    failure-isolated.
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import scenarios, then, when, given

from agency.engine import Engine

scenarios("features/typed_spine.feature")


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


def _store(engine):
    return engine.memory.entities


def _live_edges(engine):
    """Distinct (src, rel, dst) live edges from the authoritative graph."""
    rows = engine.memory.g.query(
        "MATCH (a)-[r]->(b) RETURN a.id AS s, type(r) AS rel, b.id AS d")
    return {(r["s"], r["rel"], r["d"]) for r in rows}


# ── when ──────────────────────────────────────────────────────────────────────

@when("an invocation serving an intent produces an artefact serving it")
def _inv_produces_artefact(engine, ctx):
    iid = engine.intent.capture("spine", "artefact provenance", "fk chains")
    engine.intent.confirm(iid)
    inv = engine.memory.record("Invocation",
                               {"capability": "c", "verb": "v", "role": "act"})
    engine.memory.link(inv, iid, "SERVES")
    art = engine.memory.record("Artefact", {"kind": "report"})
    engine.memory.link(inv, art, "PRODUCES")
    engine.memory.link(art, iid, "SERVES")
    ctx.update(iid=iid, inv=inv, art=art)


@when("an intent directly produces an artefact")
def _intent_produces_artefact(engine, ctx):
    iid = engine.intent.capture("spine", "direct produce", "no invocation")
    art = engine.memory.record("Artefact", {"kind": "doc"})
    engine.memory.link(iid, art, "PRODUCES")
    ctx.update(iid=iid, art=art)


@when("a lifecycle serving an intent is recorded")
def _lifecycle_serves(engine, ctx):
    iid = engine.intent.capture("spine", "lifecycle weave", "serves resolves")
    lid = engine.memory.record("Lifecycle", {"state": "working", "phase": "build"})
    engine.memory.link(lid, iid, "SERVES")
    ctx.update(iid=iid, lid=lid)


@when("I record two nodes and link them once")
def _link_once(engine, ctx):
    a = engine.memory.record("Invocation",
                             {"capability": "c", "verb": "v", "role": "act"})
    iid = engine.intent.capture("spine", "edge count", "plus one")
    ctx["before"] = len(_store(engine).edge_rows())
    engine.memory.link(a, iid, "SERVES")
    ctx.update(a=a, iid=iid)


@when("an Edge-spine write fails while linking")
def _edge_failure(engine, ctx, monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("forced edge-spine failure")
    monkeypatch.setattr(_store(engine), "upsert_edge_row", _boom)
    a = engine.memory.record("Invocation",
                             {"capability": "c", "verb": "v", "role": "act"})
    iid = engine.intent.capture("spine", "resilient", "edge survives")
    engine.memory.link(a, iid, "SERVES")
    ctx.update(a=a, iid=iid)


# ── then ──────────────────────────────────────────────────────────────────────

@then("the artefact's produced_by_id resolves to that invocation")
def _produced_by(engine, ctx):
    row = _store(engine).typed_row("Artefact", ctx["art"])
    assert row["produced_by_id"] == ctx["inv"]
    assert _store(engine).typed_row("Invocation", ctx["inv"]) is not None


@then("the artefact's serves_intent_id resolves to that intent")
def _artefact_serves(engine, ctx):
    row = _store(engine).typed_row("Artefact", ctx["art"])
    assert row["serves_intent_id"] == ctx["iid"]


@then("the artefact's produced_by_id is null")
def _produced_by_null(engine, ctx):
    row = _store(engine).typed_row("Artefact", ctx["art"])
    assert row is not None and row["produced_by_id"] is None


@then("the lifecycle state's serves_intent_id resolves to that intent")
def _lifecycle_serves_resolves(engine, ctx):
    row = _store(engine).typed_row("Lifecycle", ctx["lid"])
    assert row["serves_intent_id"] == ctx["iid"]
    assert _store(engine).typed_row("Intent", ctx["iid"]) is not None


@then("every live graph edge has a matching typed Edge row")
def _spine_complete(engine, ctx):
    live = _live_edges(engine)
    spine = {(r["src_id"], r["rel"], r["dst_id"]) for r in _store(engine).edge_rows()}
    assert live, "expected live edges"
    assert live <= spine, f"missing from spine: {live - spine}"


@then("the typed Edge count increased by exactly one")
def _edge_plus_one(engine, ctx):
    assert len(_store(engine).edge_rows()) == ctx["before"] + 1


@then("the new Edge row carries the src, dst, and rel")
def _edge_carries(engine, ctx):
    row = _store(engine).edge_row(ctx["a"], "SERVES", ctx["iid"])
    assert row is not None
    assert row["src_id"] == ctx["a"] and row["dst_id"] == ctx["iid"]
    assert row["rel"] == "SERVES"


@then("the authoritative graph still has the edge")
def _graph_edge_survives(engine, ctx):
    rows = engine.memory.g.query(
        "MATCH (a)-[:SERVES]->(b) WHERE a.id = $a AND b.id = $b RETURN a.id AS s",
        {"a": ctx["a"], "b": ctx["iid"]})
    assert len(rows) == 1
