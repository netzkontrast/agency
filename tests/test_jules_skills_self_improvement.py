"""Spec 013 Phase 10 — `jules-self-improvement` skill.

The dogfood loop made first-class — REBOUND in the v1-self-improvement
follow-on commit so both phases are invoke-bound to real verbs:

- Phase 1 (`collect-dogfood`) → `dogfood.collect(plan_dir)` walks
  `Plan/**/DOGFOOD-NOTES.md` and returns observations + a flat text list.
- Phase 2 (`fold-into-graph`) → `reflect.batch_note(scope, texts)` bulk-
  records one Reflection node per text in a single invocation (no longer
  capped at one-observation-per-walk like the original `reflect.note`
  binding).
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
        "collect-dogfood", "fold-into-graph",
    ]


def test_skill_has_no_hard_gate(engine):
    sk = engine.ontology.skill("jules-self-improvement")
    assert not any(p.get("gate") == "hard" for p in sk["phases"])


def test_walk_records_phase_provenance(engine, iid, tmp_path):
    plan_root = tmp_path / "Plan"
    (plan_root / "777-fix").mkdir(parents=True)
    (plan_root / "777-fix" / "DOGFOOD-NOTES.md").write_text(
        "**Observation 1 — x.** x body."
    )
    sk = engine.ontology.skill("jules-self-improvement")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    run.submit({"plan_dir": str(plan_root)})
    run.submit({"scope": "observation", "texts": ["x body"]})
    rows = engine.memory.g.query(
        "MATCH (s:Skill)-[:HAS_PHASE]->(p:Phase) "
        "WHERE s.name = $sn RETURN p",
        {"sn": "jules-self-improvement"},
    )
    assert len(rows) == 2
