"""Spec 041 — Superpowers discipline ports (current-model: walkable skills + references)."""
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
    i = engine.intent.capture("ship", "a feature", "tests green")
    engine.intent.confirm(i)
    return i


def _call(e, iid, cap, verb, **kw):
    res, _ = e.registry.invoke(e.memory, iid, cap, verb, **kw)
    return res["result"] if isinstance(res, dict) and "result" in res else res


def test_new_disciplines_registered_lint_and_walk(engine, iid):
    cases = [("delegate", "dispatching-parallel-agents"), ("subagent", "subagent-driven-development")]
    for cap, skill in cases:
        assert skill in engine.registry.get(cap).ontology.skills
        assert _call(engine, iid, "skills", "lint", skill_name=skill)["ok"] is True
        res, _ = engine.registry.invoke(engine.memory, iid, "develop", "skill_walk",
                                        name=skill, inputs={})
        out = res["result"] if isinstance(res, dict) and "result" in res else res
        assert out.get("status") in ("completed", "input-required", "blocked", "failed")


def test_no_dangling_verb_in_the_disciplines(engine):
    # every `<cap>.<verb>` named in a phase must be a real verb (guards a future rename)
    for cap, skill in (("delegate", "dispatching-parallel-agents"),
                       ("subagent", "subagent-driven-development")):
        sk = engine.registry.get(cap).ontology.skills[skill]
        for p in sk["phases"]:
            for ref in p.get("verbs", []):
                c, v = ref.split(".", 1)
                assert v in engine.registry.get(c).verbs, f"dangling {ref}"


def test_deepening_references_resolve(engine, iid):
    for topic in ("testing-anti-patterns", "debugging-anti-patterns"):
        out = _call(engine, iid, "develop", "reference", topic=topic)
        doc = out["doc"] if isinstance(out, dict) else out
        assert isinstance(doc, str) and len(doc) > 50 and "#" in doc


def test_disciplines_are_suggestable(engine, iid):
    out = _call(engine, iid, "intent", "suggests",
                called_state="fan out across multiple independent domains in parallel")
    assert out["skill"] == "dispatching-parallel-agents"
