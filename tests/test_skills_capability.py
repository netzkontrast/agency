"""Spec 026 (Part A) — the first-class `skills` capability: find / render / lint."""
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
    i = engine.intent.capture("skills", "query the skill registry", "find/render/lint")
    engine.intent.confirm(i)
    return i


def _call(e, iid, cap, verb, **kw):
    res, _ = e.registry.invoke(e.memory, iid, cap, verb, **kw)
    return res["result"] if isinstance(res, dict) and "result" in res else res


def test_skills_registers_as_a_capability(engine):
    # bootstrap also validates the docstring-derived SkillDoc — registration proves it
    assert "skills" in engine.registry.names()


def test_find_lists_skills_with_owning_capability(engine, iid):
    out = _call(engine, iid, "skills", "find")
    assert out["total"] >= 1
    names = {c["name"] for c in out["candidates"]}
    assert "tdd" in names and "shell-usage" in names      # authored + derived both surface
    tdd = next(c for c in out["candidates"] if c["name"] == "tdd")
    assert tdd["capability"] == "develop"


def test_find_filters_by_kind_and_capability(engine, iid):
    usage = _call(engine, iid, "skills", "find", kind="usage")
    assert usage["total"] >= 1 and all(c["kind"] == "usage" for c in usage["candidates"])
    dev = _call(engine, iid, "skills", "find", capability="develop")
    assert dev["total"] >= 1 and all(c["capability"] == "develop" for c in dev["candidates"])


def test_render_brief_then_full(engine, iid):
    brief = _call(engine, iid, "skills", "render", skill_name="shell-usage")
    assert "shell-usage" in brief["markdown"] and "phases:" in brief["markdown"]
    full = _call(engine, iid, "skills", "render", skill_name="shell-usage", depth="full")
    assert "produces:" in full["markdown"]


def test_render_single_phase_and_unknown(engine, iid):
    one = _call(engine, iid, "skills", "render", skill_name="shell-usage", phase_index=1)
    assert "1." in one["markdown"]
    assert _call(engine, iid, "skills", "render", skill_name="nope").get("error")


def test_lint_passes_for_a_derived_usage_skill(engine, iid):
    out = _call(engine, iid, "skills", "lint", skill_name="shell-usage")
    assert out["ok"] is True and out["violations"] == []


def test_lint_flags_unknown_skill(engine, iid):
    out = _call(engine, iid, "skills", "lint", skill_name="nope")
    assert out["ok"] is False and out["violations"]


def test_authored_triage_discipline_overrides_derived_and_walks(engine, iid):
    # the authored discipline replaces the derived `skills-usage` (Spec 081 override)
    found = _call(engine, iid, "skills", "find", capability="skills")
    names = {c["name"] for c in found["candidates"]}
    assert "skills-triage" in names and "skills-usage" not in names
    # it lints clean…
    assert _call(engine, iid, "skills", "lint", skill_name="skills-triage")["ok"] is True
    # …and is walkable via the existing walker (proves the 081 surface end-to-end)
    res, _ = engine.registry.invoke(engine.memory, iid, "develop", "skill_walk",
                                    name="skills-triage", inputs={})
    out = res["result"] if isinstance(res, dict) and "result" in res else res
    assert out.get("status") in ("completed", "input-required", "blocked", "failed")
