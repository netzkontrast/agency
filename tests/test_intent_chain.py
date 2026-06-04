"""Spec 048 — Intent chaining via PARENT_INTENT edge.

Three properties: parent-edge correctness, root vs leaf classification,
cycle detection.
"""
import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


def test_root_intent_has_no_parent(engine):
    iid = engine.intent.capture("root", "x", "x")
    engine.intent.confirm(iid)
    # The Intent's parent_intent_id is empty for roots.
    rows = engine.memory.find("Intent")
    me = next(r for r in rows if r["id"] == iid)
    assert me.get("parent_intent_id", "") == ""


def test_child_intent_records_parent(engine):
    parent = engine.intent.capture("parent", "x", "x")
    engine.intent.confirm(parent)
    child = engine.intent.capture("child", "x", "x",
                                   parent_intent_id=parent)
    engine.intent.confirm(child)
    rows = engine.memory.find("Intent")
    me = next(r for r in rows if r["id"] == child)
    assert me["parent_intent_id"] == parent


def test_parent_intent_edge_recorded(engine):
    parent = engine.intent.capture("p", "x", "x")
    engine.intent.confirm(parent)
    child = engine.intent.capture("c", "x", "x", parent_intent_id=parent)
    engine.intent.confirm(child)
    # The PARENT_INTENT edge: child → parent.
    rows = engine.memory.g.query(
        "MATCH (c:Intent)-[:PARENT_INTENT]->(p:Intent) "
        "WHERE c.id = $cid RETURN p",
        {"cid": child})
    assert len(rows) == 1
    assert rows[0]["p"]["properties"]["id"] == parent


def test_three_level_chain(engine):
    grand = engine.intent.capture("grand", "x", "x")
    engine.intent.confirm(grand)
    parent = engine.intent.capture("parent", "x", "x",
                                    parent_intent_id=grand)
    engine.intent.confirm(parent)
    child = engine.intent.capture("child", "x", "x",
                                   parent_intent_id=parent)
    engine.intent.confirm(child)
    # Walk up from child to grand.
    rows = engine.memory.g.query(
        "MATCH (c:Intent)-[:PARENT_INTENT*1..3]->(g:Intent) "
        "WHERE c.id = $cid AND g.id = $gid RETURN g",
        {"cid": child, "gid": grand})
    assert len(rows) >= 1


def test_cycle_detection_two_intent_loop(engine):
    """Cycle: A → B → A. capture() must refuse to record."""
    a = engine.intent.capture("a", "x", "x")
    engine.intent.confirm(a)
    b = engine.intent.capture("b", "x", "x", parent_intent_id=a)
    engine.intent.confirm(b)
    # Now try to AMEND A so its parent is B (would create A → B → A).
    # Since we don't amend parents directly, instead try to capture a
    # new C whose parent claims to be A but ALSO transitively through B
    # back to itself. The simplest test: capture into a chain where
    # the parent_intent_id ALREADY is the new node id — which can't
    # happen via capture (id is minted inside), so we test the helper
    # directly.
    with pytest.raises(ValueError, match="cycle"):
        engine.intent._check_no_cycle(parent_id=b, new_id=a)


def test_cycle_detection_self_loop(engine):
    a = engine.intent.capture("a", "x", "x")
    engine.intent.confirm(a)
    with pytest.raises(ValueError, match="cycle"):
        engine.intent._check_no_cycle(parent_id=a, new_id=a)


def test_pathological_depth_fails_loud(engine):
    """A chain deeper than 32 fails loud — the depth itself is a smell."""
    chain = []
    prev = ""
    for i in range(33):
        iid = engine.intent.capture(f"n{i}", "x", "x",
                                     parent_intent_id=prev)
        engine.intent.confirm(iid)
        chain.append(iid)
        prev = iid
    # Now attempt to make a 34th. The cycle-check should refuse.
    with pytest.raises(ValueError, match="too deep"):
        engine.intent.capture("too-deep", "x", "x",
                              parent_intent_id=prev)
