"""Spec 013 Phase 10 — `jules-self-improvement` skill.

The dogfood loop made first-class. Two advisory phases: `collect-dogfood`
(document phase, caller supplies observations) and `fold-into-spec`
(invoke-bound to `reflect.note(scope, text)` so each observation lands
as a `Reflection` node in the bi-temporal graph).
"""
import tempfile

import pytest

from agency.engine import Engine
from agency.skill import SkillRun


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def iid(engine):
    intent = engine.intent.capture(
        "fold dogfood observations into the graph",
        "Reflection nodes land scoped to 'observation'",
        "every observation produces a memorable artefact",
    )
    engine.intent.confirm(intent)
    return intent


def test_skill_registered_on_jules_ontology(engine):
    assert "jules-self-improvement" in engine.ontology.skills
    sk = engine.ontology.skill("jules-self-improvement")
    assert [p["name"] for p in sk["phases"]] == [
        "collect-dogfood", "fold-into-spec",
    ]


def test_skill_has_no_hard_gate(engine):
    sk = engine.ontology.skill("jules-self-improvement")
    assert not any(p.get("gate") == "hard" for p in sk["phases"])


def test_walk_produces_reflection_node_via_reflect_note(engine, iid):
    sk = engine.ontology.skill("jules-self-improvement")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    obs = "Jules's auto-reaction emoji didn't fire a webhook; only the reply_to_pr_comments did."
    run.submit({"observations": [obs]})
    res = run.submit({"scope": "observation", "text": obs})
    assert res["status"] == "completed"

    # reflect.note recorded a Reflection node in the graph.
    rows = engine.memory.g.query(
        "MATCH (r:Reflection) WHERE r.scope = $sc RETURN r",
        {"sc": "observation"},
    )
    assert len(rows) == 1
    assert obs in rows[0]["r"]["properties"]["text"]


def test_walk_records_phase_provenance(engine, iid):
    sk = engine.ontology.skill("jules-self-improvement")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    run.submit({"observations": ["x"]})
    run.submit({"scope": "observation", "text": "x"})
    rows = engine.memory.g.query(
        "MATCH (s:Skill)-[:HAS_PHASE]->(p:Phase) "
        "WHERE s.name = $sn RETURN p",
        {"sn": "jules-self-improvement"},
    )
    assert len(rows) == 2
