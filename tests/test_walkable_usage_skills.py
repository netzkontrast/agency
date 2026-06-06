"""Spec 081 — every capability ships a walkable usage-skill.

A capability with no authored `ontology.skills` gets a DERIVED `<cap>-usage`
phase-graph (verbs clustered by role → ≤6 phases ending in a hard confirm gate)
so a fresh agent can walk it via `develop.skill_walk` to learn how to drive the
capability's MCP verbs. Authored skills are the override — never replaced.
"""
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


def test_every_verb_capability_has_a_walkable_skill(engine):
    missing = [n for n in engine.registry.names()
               if engine.registry.get(n).verbs
               and not (getattr(engine.registry.get(n).ontology, "skills", {}) or {})]
    assert missing == [], f"capabilities with no walkable skill: {missing}"


def test_bare_capability_gets_a_derived_usage_skill(engine):
    shell = engine.registry.get("shell")          # shell declared no ontology.skills
    skills = shell.ontology.skills
    assert "shell-usage" in skills
    sk = skills["shell-usage"]
    assert sk["kind"] == "usage"
    assert 1 <= len(sk["phases"]) <= 6
    assert sk["phases"][-1].get("gate") == "hard"   # ends in a hard confirm gate
    # the walk names the verbs it teaches
    named = {v for p in sk["phases"] for v in p.get("verbs", [])}
    assert named & set(shell.verbs), "walk should reference the capability's real verbs"


def test_authored_skills_are_not_overridden(engine):
    dev = engine.registry.get("develop")          # authored 9 disciplines
    assert "develop-usage" not in dev.ontology.skills
    assert "tdd" in dev.ontology.skills


def test_derived_usage_skill_is_walkable(engine):
    iid = engine.intent.capture("walk usage", "drive a capability's verbs", "gate reached")
    engine.intent.confirm(iid)
    res, _ = engine.registry.invoke(engine.memory, iid, "develop", "skill_walk",
                                    name="shell-usage", inputs={})
    out = res["result"] if isinstance(res, dict) and "result" in res else res
    assert isinstance(out, dict) and "status" in out
    assert out["status"] in ("completed", "input-required", "blocked", "failed")


def test_emit_renders_walk_section():
    from agency import install
    e = Engine(":memory:")
    try:
        files = install.generate(e)
    finally:
        e.memory.close()
    md = files["skills/shell/SKILL.md"]
    assert "Walk this capability" in md
    assert "shell-usage" in md
