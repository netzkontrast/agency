"""Spec 013 Phase 6 — `jules-tool-discipline` skill (collapsed).

Phase C REVIEW must-fix #5: the original 5-phase shape was tautological
(``was this string in the prompt?`` × 5 isn't a skill). The collapsed
shape is 1 advisory phase bound to `jules.lint_prompt`. Reusable from
inside `jules-protocol-preamble` Phase 3 OR standalone when the caller
wants to lint a draft prompt without committing to a dispatch.
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
        "lint a dispatch prompt for canonical-tool naming",
        "skill walks via lint_prompt; reports missing tools",
        "no false positives on a canonical prompt",
    )
    engine.intent.confirm(intent)
    return intent


def test_skill_registered_on_jules_ontology(engine):
    assert "jules-tool-discipline" in engine.ontology.skills
    sk = engine.ontology.skill("jules-tool-discipline")
    assert [p["name"] for p in sk["phases"]] == ["apply-tool-discipline"]


def test_skill_has_no_hard_gate(engine):
    sk = engine.ontology.skill("jules-tool-discipline")
    assert not any(p.get("gate") == "hard" for p in sk["phases"])


def test_walks_to_completion_on_canonical_prompt(engine, iid):
    canonical = (
        "Use pre_commit_instructions(), then submit(...). "
        "Use request_user_input for blocking asks. "
        "Use replace_with_git_merge_diff for multi-line edits. "
        "Call request_code_review before submit."
    )
    sk = engine.ontology.skill("jules-tool-discipline")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    res = run.submit({"text": canonical, "must_name": ""})
    assert res["status"] == "completed"
    assert run.done


def test_walks_to_completion_even_with_missing_tools(engine, iid):
    """`jules.lint_prompt` returns a truthy dict regardless of `ok`, so the
    skill walk advances. The lint VERDICT lives in the lint_result dict —
    callers inspect ok/missing/extras to decide. (Hard-gating on the lint
    result is OOS for v1; tracked in DESIGN.md Open Questions.)"""
    sk = engine.ontology.skill("jules-tool-discipline")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    res = run.submit({"text": "open a PR when done", "must_name": ""})
    assert res["status"] == "completed"
    assert run.done


def test_records_provenance_phase_node(engine, iid):
    sk = engine.ontology.skill("jules-tool-discipline")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    run.submit({"text": "x", "must_name": ""})
    rows = engine.memory.g.query(
        "MATCH (s:Skill)-[:HAS_PHASE]->(p:Phase) "
        "WHERE s.name = $sn RETURN p",
        {"sn": "jules-tool-discipline"},
    )
    assert len(rows) == 1
    assert rows[0]["p"]["properties"]["name"] == "apply-tool-discipline"


def test_caller_can_scope_must_name_override(engine, iid):
    """Comma-separated `must_name` lets a caller scope the predicate to a
    smaller set (e.g. only the publish pair). End-to-end check that the
    skill walk forwards the override correctly into jules.lint_prompt."""
    sk = engine.ontology.skill("jules-tool-discipline")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    res = run.submit({
        "text": "Use pre_commit_instructions() then submit(...).",
        "must_name": "pre_commit_instructions,submit",
    })
    assert res["status"] == "completed"
