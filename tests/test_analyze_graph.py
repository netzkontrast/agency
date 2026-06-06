"""Spec 084 — analyze.graph: a first-class graph-query verb (read the graph)."""
import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        yield e
    finally:
        e.memory.close()


@pytest.fixture
def iid(engine):
    i = engine.intent.capture("graph query", "read the graph", "census + typed nodes")
    engine.intent.confirm(i)
    return i


def _call(e, iid, cap, verb, **kw):
    res, _ = e.registry.invoke(e.memory, iid, cap, verb, **kw)
    return res["result"] if isinstance(res, dict) and "result" in res else res


def test_graph_census_counts_live_nodes(engine, iid):
    out = _call(engine, iid, "analyze", "graph")
    assert out["census"].get("Intent", 0) >= 1     # the confirmed intent is in the graph
    assert out["nodes"] == []                       # no node_type → census only


def test_graph_lists_a_label_filtered_by_scope(engine, iid):
    engine.registry.invoke(engine.memory, iid, "reflect", "note",
                           scope="observation", text="a recorded lesson")
    out = _call(engine, iid, "analyze", "graph", node_type="Reflection", scope="observation")
    assert out["nodes"], "should list the recorded reflection"
    assert all(n.get("scope") == "observation" for n in out["nodes"])
    assert out["census"].get("Reflection", 0) >= 1


def test_graph_limit_caps_rows(engine, iid):
    for i in range(4):
        engine.registry.invoke(engine.memory, iid, "reflect", "note",
                               scope="observation", text=f"note {i}")
    out = _call(engine, iid, "analyze", "graph", node_type="Reflection", limit=2)
    assert len(out["nodes"]) == 2
