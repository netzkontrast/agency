"""Spec 026 — skills.index promotes ontology.skills → Skill/Phase graph nodes."""
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
    i = engine.intent.capture("index", "promote skills to the graph", "Skill+Phase nodes")
    engine.intent.confirm(i)
    return i


def _call(e, iid, cap, verb, **kw):
    res, _ = e.registry.invoke(e.memory, iid, cap, verb, **kw)
    return res["result"] if isinstance(res, dict) and "result" in res else res


def test_index_promotes_skills_and_phases(engine, iid):
    out = _call(engine, iid, "skills", "index")
    assert out["skills"] >= 1 and out["phases"] >= 1
    # analyze.graph now sees them — skills are first-class graph citizens
    census = _call(engine, iid, "analyze", "graph")["census"]
    assert census.get("Skill", 0) == out["skills"]
    assert census.get("Phase", 0) == out["phases"]


def test_skill_node_carries_name_and_kind(engine, iid):
    _call(engine, iid, "skills", "index")
    node = engine.memory.recall("skill:skills-triage")
    assert node and node.get("kind") == "discipline"
    # its phases were linked
    p1 = engine.memory.recall("phase:skills-triage:1")
    assert p1 and p1.get("skill") == "skills-triage"


def test_index_is_idempotent(engine, iid):
    a = _call(engine, iid, "skills", "index")
    b = _call(engine, iid, "skills", "index")
    assert a == b                                   # same counts, no duplicate nodes
    census = _call(engine, iid, "analyze", "graph")["census"]
    assert census["Skill"] == a["skills"]           # re-index upserted, didn't duplicate
