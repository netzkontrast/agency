"""Acceptance — CapabilityContext.neighbors() one-hop edge traversal (Spec 125).

Converted from tests/test_context_neighbors.py. Behaviour: property dicts
returned, direction semantics, limit, empty/unknown cases, parity with
find()+filter. The test_neighbors_method_exists structural check is dropped
(review/API-cleanliness concern, not observable behaviour).
"""
from __future__ import annotations

import pytest
from pytest_bdd import given, scenarios, then, when

from conftest import invoke
from agency.capability import CapabilityContext

scenarios("features/context_neighbors.feature")


# ── helpers ────────────────────────────────────────────────────────────────

def _ctx(engine, iid):
    return CapabilityContext(
        memory=engine.memory,
        ontology=engine.registry.ontology,
        registry=engine.registry,
        intent_id=iid,
        agent_id="agent:test",
        client=None,
        depth=0,
        engine=engine,
        drivers=None,
    )


# ── shared Given step ──────────────────────────────────────────────────────

@given("a novel with two chapters", target_fixture="novel_and_chapters")
def _novel_two_chapters(engine, confirmed_intent):
    iid = confirmed_intent
    novel_id = invoke(engine, iid, "novel", "create_novel",
                      title="Test Novel", author="A.N. Author")[0]["novel_id"]
    ch1 = invoke(engine, iid, "novel", "create_chapter",
                 novel_id=novel_id, number=1, title="Ch 1")[0]["chapter_id"]
    ch2 = invoke(engine, iid, "novel", "create_chapter",
                 novel_id=novel_id, number=2, title="Ch 2")[0]["chapter_id"]
    return {"novel_id": novel_id, "ch1": ch1, "ch2": ch2}


# ── When steps ─────────────────────────────────────────────────────────────

@when("I traverse CHAPTER_OF edges inward from the novel",
      target_fixture="neighbors")
def _traverse_in(engine, confirmed_intent, novel_and_chapters):
    ctx = _ctx(engine, confirmed_intent)
    return ctx.neighbors(novel_and_chapters["novel_id"], "CHAPTER_OF", direction="in")


@when("I traverse CHAPTER_OF edges from the novel using the default direction",
      target_fixture="neighbors")
def _traverse_default(engine, confirmed_intent, novel_and_chapters):
    ctx = _ctx(engine, confirmed_intent)
    return ctx.neighbors(novel_and_chapters["novel_id"], "CHAPTER_OF")


@when("I traverse CHAPTER_OF edges outward from a chapter",
      target_fixture="out_neighbors")
def _traverse_out(engine, confirmed_intent, novel_and_chapters):
    ctx = _ctx(engine, confirmed_intent)
    return ctx.neighbors(novel_and_chapters["ch1"], "CHAPTER_OF", direction="out")


@when("I traverse a NONEXISTENT_EDGE from the novel",
      target_fixture="empty_neighbors")
def _traverse_missing_edge(engine, confirmed_intent, novel_and_chapters):
    ctx = _ctx(engine, confirmed_intent)
    return ctx.neighbors(novel_and_chapters["novel_id"], "NONEXISTENT_EDGE")


@when("I traverse CHAPTER_OF from a node id that does not exist",
      target_fixture="empty_neighbors")
def _traverse_unknown_id(engine, confirmed_intent):
    ctx = _ctx(engine, confirmed_intent)
    return ctx.neighbors("novel:does-not-exist", "CHAPTER_OF")


@when("I traverse CHAPTER_OF with direction sideways")
def _traverse_bad_direction(engine, confirmed_intent, novel_and_chapters):
    pass  # the Then step does the assertion


@when("I traverse CHAPTER_OF with limit 1", target_fixture="capped")
def _traverse_limit(engine, confirmed_intent, novel_and_chapters):
    ctx = _ctx(engine, confirmed_intent)
    return ctx.neighbors(novel_and_chapters["novel_id"], "CHAPTER_OF", limit=1)


@when("I list chapters using find-plus-filter", target_fixture="find_filter")
def _find_filter(engine, confirmed_intent, novel_and_chapters):
    ctx = _ctx(engine, confirmed_intent)
    novel_id = novel_and_chapters["novel_id"]
    return sorted(c["id"] for c in ctx.find("Chapter") if c.get("novel") == novel_id)


# ── Then steps ─────────────────────────────────────────────────────────────

@then("2 property dicts are returned")
def _two_dicts(neighbors):
    assert len(neighbors) == 2, f"expected 2, got {len(neighbors)}"


@then("each dict has an id key")
def _has_id(neighbors):
    for d in neighbors:
        assert "id" in d, f"dict missing 'id': {d}"


@then("1 property dict is returned")
def _one_dict(out_neighbors):
    assert len(out_neighbors) == 1, f"expected 1, got {len(out_neighbors)}"


@then("the returned node id matches the novel")
def _matches_novel(out_neighbors, novel_and_chapters):
    assert out_neighbors[0]["id"] == novel_and_chapters["novel_id"]


@then("an empty list is returned")
def _empty(empty_neighbors):
    assert empty_neighbors == []


@then("a ValueError is raised")
def _val_err(engine, confirmed_intent, novel_and_chapters):
    ctx = _ctx(engine, confirmed_intent)
    with pytest.raises(ValueError):
        ctx.neighbors(novel_and_chapters["novel_id"], "CHAPTER_OF",
                      direction="sideways")


@then("at most 1 property dict is returned")
def _at_most_one(capped):
    assert len(capped) <= 1


@then("both results contain the same chapter ids")
def _parity(neighbors, find_filter):
    via_n = sorted(d["id"] for d in neighbors)
    assert via_n == find_filter
