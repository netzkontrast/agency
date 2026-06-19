"""Acceptance — Spec 328: typed Intent fulfilment (the Intent-owned Gate +
AcceptanceCriterion).

Behaviour under test:
  - confirming an Intent records a typed clarity Gate keyed to that Intent, whose
    score equals the shipped substrate clarity score (Spec 322 — single source);
  - re-checking after sharpening accrues Gate history (a new, higher-scored row);
  - an AcceptanceCriterion is typed + foreign-keyed to its Intent (VALIDATES);
  - a Lifecycle-attached gate (no intent edge) is NOT mis-attributed to an intent.
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import scenarios, then, when, given

from agency.engine import Engine

scenarios("features/typed_fulfilment.feature")


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


def _gates_for(engine, iid):
    rows = [r for r in _store(engine).typed_rows("Gate")
            if r.get("intent_id") == iid and r.get("kind") == "clarity"]
    return sorted(rows, key=lambda r: r["vfrom"])


# ── when ──────────────────────────────────────────────────────────────────────

@when("I capture and confirm an intent")
def _capture_confirm(engine, ctx):
    iid = engine.intent.capture("fulfil", "typed fulfilment", "gate recorded")
    engine.intent.confirm(iid)
    ctx["iid"] = iid


@when("I add a measurable acceptance criterion and re-confirm")
def _add_criterion_reconfirm(engine, ctx):
    cid = engine.memory.record("AcceptanceCriterion", {
        "text": "the row exists", "gherkin": "Given X When Y Then Z",
        "measurable": True})
    engine.memory.link(cid, ctx["iid"], "VALIDATES")
    engine.intent.confirm(ctx["iid"])


@when("I capture an intent and add a measurable acceptance criterion to it")
def _capture_add_criterion(engine, ctx):
    iid = engine.intent.capture("ac", "criterion typed", "fk set")
    cid = engine.memory.record("AcceptanceCriterion", {
        "text": "must render", "gherkin": "Given a node When render Then a file",
        "measurable": True})
    engine.memory.link(cid, iid, "VALIDATES")
    ctx["iid"], ctx["cid"] = iid, cid


@when("I record a Lifecycle gate not tied to any intent")
def _lifecycle_gate(engine, ctx):
    lid = engine.memory.record("Lifecycle", {"state": "working", "phase": "x"})
    gid = engine.memory.record("Gate", {"name": "human-confirm", "passed": True})
    engine.memory.link(lid, gid, "PASSED")
    ctx["gid"] = gid


# ── then ──────────────────────────────────────────────────────────────────────

@then("a typed clarity Gate exists for that intent")
def _gate_exists(engine, ctx):
    assert _gates_for(engine, ctx["iid"]), "expected a clarity Gate row"


@then("the clarity Gate's intent_id resolves to a typed Intent row")
def _gate_intent_resolves(engine, ctx):
    g = _gates_for(engine, ctx["iid"])[-1]
    assert _store(engine).typed_row("Intent", g["intent_id"]) is not None


@then("the clarity Gate's score equals the intent's substrate clarity score")
def _gate_score_matches(engine, ctx):
    from agency._clarity import clarity_score
    g = _gates_for(engine, ctx["iid"])[-1]
    assert abs(g["score"] - clarity_score(engine.memory, ctx["iid"])) < 1e-6


@then("the intent has more than one clarity Gate")
def _more_than_one(engine, ctx):
    assert len(_gates_for(engine, ctx["iid"])) > 1


@then("the latest clarity Gate's score is higher than the first")
def _score_rose(engine, ctx):
    gates = _gates_for(engine, ctx["iid"])
    assert gates[-1]["score"] > gates[0]["score"]


@then("the criterion has a typed AcceptanceCriterion row")
def _criterion_row(engine, ctx):
    assert _store(engine).typed_row("AcceptanceCriterion", ctx["cid"]) is not None


@then("the criterion row's intent_id resolves to that intent")
def _criterion_fk(engine, ctx):
    row = _store(engine).typed_row("AcceptanceCriterion", ctx["cid"])
    assert row["intent_id"] == ctx["iid"]


@then("the criterion row's measurable flag is true")
def _criterion_measurable(engine, ctx):
    row = _store(engine).typed_row("AcceptanceCriterion", ctx["cid"])
    assert row["measurable"] is True


@then("that Gate row has a null intent_id")
def _lifecycle_gate_null(engine, ctx):
    row = _store(engine).typed_row("Gate", ctx["gid"])
    assert row is not None and row["intent_id"] is None
