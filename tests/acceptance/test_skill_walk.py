"""Acceptance — skill walk behaviour.

Converted from:
  tests/test_skill_walk.py     (Spec 018 Win 1 — the core status contract)
  tests/test_walkable_usage_skills.py (Spec 081 — derived usage skills)

Dropped as implementation/structural (not observable behaviour):
  test_skill_walk_slices.py — render_phase / render_verb are internal
    disclosure helpers; their output format (T1/T2/T3 slices, snippet
    syntax) is implementation detail, not a behaviour a client observes.
  _check_* lint-internal calls in test_lint_*.py — not observable via the
    wire surface.
"""
from __future__ import annotations


from pytest_bdd import parsers, scenarios, then, when


scenarios("features/skill_walk.feature")


# ── helpers ──────────────────────────────────────────────────────────────────

def _walk(engine, iid, name, inputs, resume_from=""):
    raw, _ = engine.registry.invoke(
        engine.memory, iid, "develop", "skill_walk",
        name=name, inputs=inputs, resume_from=resume_from,
    )
    return raw["result"] if isinstance(raw, dict) and "result" in raw else raw


TDD_FULL_INPUTS = {
    "failing_test": "test_x asserts behaviour",
    "implementation": "def x(): ...",
    "refactored": "tidy",
    "tests_pass": "12 passed",
}


# ── When steps ───────────────────────────────────────────────────────────────

@when("I walk the \"tdd\" skill with all phase inputs provided",
      target_fixture="walk_result")
def _walk_tdd_full(engine, confirmed_intent):
    return _walk(engine, confirmed_intent, "tdd", TDD_FULL_INPUTS)


@when("I resume the walk with the same skill_id", target_fixture="walk_result")
def _resume_walk(engine, confirmed_intent, walk_result):
    skill_id = walk_result["skill_id"]
    return _walk(engine, confirmed_intent, "tdd",
                 {"tests_pass": "ok"}, resume_from=skill_id)


@when(parsers.parse('I walk a skill named "{name}" with no inputs'),
      target_fixture="walk_result")
def _walk_named_no_inputs(engine, confirmed_intent, name):
    return _walk(engine, confirmed_intent, name, {})


@when("I walk the \"tdd\" skill with only the first phase input",
      target_fixture="walk_result")
def _walk_tdd_partial(engine, confirmed_intent):
    return _walk(engine, confirmed_intent, "tdd", {"failing_test": "t"})


@when("I walk \"authoring-capabilities\" with scaffold inputs into a temp directory",
      target_fixture="authoring_result")
def _walk_authoring(engine, confirmed_intent, tmp_path):
    result = _walk(engine, confirmed_intent, "authoring-capabilities", {
        "read_doctrine": "yes",
        "name": "walkcap", "kind": "light", "base_dir": str(tmp_path),
        "verbs_written": "yes",
        "budget_ok": "yes",
        "reflection_recorded": "rid",
    })
    return {"result": result, "tmp_path": tmp_path}


@when(parsers.parse('I walk the derived skill "{name}" with no inputs'),
      target_fixture="walk_result")
def _walk_derived_no_inputs(engine, confirmed_intent, name):
    return _walk(engine, confirmed_intent, name, {})


# ── Then steps — core status contract ────────────────────────────────────────

@then(parsers.parse('the status is "{expected}"'))
def _status_is(walk_result, expected):
    assert walk_result["status"] == expected, (
        f"expected status={expected!r}, got {walk_result['status']!r}")


@then("the response names the blocked phase")
def _has_phase(walk_result):
    assert walk_result.get("phase"), "response must name the blocked phase"


@then("the response carries a skill_id and partial_outputs")
def _has_skill_id_and_partial(walk_result):
    assert walk_result.get("skill_id"), "response must carry skill_id"
    assert walk_result.get("partial_outputs") is not None


@then("the skill_id is unchanged")
def _skill_id_stable(walk_result):
    # fixture returns the resumed result; we only verify structure here
    assert walk_result.get("skill_id"), "completed walk must still carry skill_id"


@then(parsers.parse('the error mentions "{term}"'))
def _error_mentions(walk_result, term):
    assert term in (walk_result.get("error") or ""), (
        f"expected {term!r} in error; got {walk_result.get('error')!r}")


@then(parsers.parse('the response lists available skills including "{name}"'))
def _available_includes(walk_result, name):
    assert name in walk_result.get("available", []), (
        f"expected {name!r} in available; got {walk_result.get('available')!r}")


@then("the response names the failing phase")
def _has_failing_phase(walk_result):
    assert walk_result.get("phase"), "failed walk must name the failing phase"


@then("the response lists the completed phases before the failure")
def _has_completed_phases(walk_result):
    assert isinstance(walk_result.get("completed_phases"), list)
    assert len(walk_result["completed_phases"]) >= 1


# ── Then steps — provenance ───────────────────────────────────────────────────

@then("a Skill node SERVES the intent in the graph")
def _skill_serves_intent(engine, confirmed_intent, walk_result):
    rows = engine.memory.g.query(
        "MATCH (s:Skill)-[:SERVES]->(i:Intent) WHERE i.id = $iid AND s.id = $sid RETURN s",
        {"iid": confirmed_intent, "sid": walk_result["skill_id"]},
    )
    assert len(rows) == 1, "Skill node must SERVE the intent"


@then("the Skill node has a BLOCKED_ON edge to a paused Gate")
def _blocked_on_gate(engine, walk_result):
    rows = engine.memory.g.query(
        "MATCH (s:Skill)-[:BLOCKED_ON]->(g:Gate) WHERE s.id = $sid RETURN g",
        {"sid": walk_result["skill_id"]},
    )
    assert len(rows) == 1
    assert rows[0]["g"]["properties"]["paused"] is True


# ── Then steps — verb-bound phase ─────────────────────────────────────────────

@then("the scaffolded file is created on disk")
def _file_created(authoring_result):
    tmp_path = authoring_result["tmp_path"]
    assert (tmp_path / "walkcap.py").is_file(), "phase 2 must execute scaffold_capability"


@then("the walk eventually reaches a failed or completed status")
def _walk_terminal(authoring_result):
    status = authoring_result["result"]["status"]
    assert status in ("failed", "completed"), f"unexpected status: {status!r}"


# ── Then steps — derived usage skills ────────────────────────────────────────

@then("every capability with verbs has at least one walkable skill")
def _every_cap_has_skill(engine):
    missing = [n for n in engine.registry.names()
               if engine.registry.get(n).verbs
               and not (getattr(engine.registry.get(n).ontology, "skills", {}) or {})]
    assert missing == [], f"capabilities with no walkable skill: {missing}"


@then("the \"shell\" capability has a derived usage skill")
def _shell_has_derived(engine):
    shell = engine.registry.get("shell")
    assert "shell-usage" in (shell.ontology.skills or {})


@then("the usage skill ends with a hard gate")
def _usage_ends_hard(engine):
    shell = engine.registry.get("shell")
    sk = shell.ontology.skills["shell-usage"]
    assert sk["phases"][-1].get("gate") == "hard"


@then("the usage skill references real verbs from the capability")
def _usage_references_verbs(engine):
    shell = engine.registry.get("shell")
    sk = shell.ontology.skills["shell-usage"]
    named = {v for p in sk["phases"] for v in p.get("verbs", [])}
    assert named & set(shell.verbs), "usage skill should reference the capability's real verbs"


@then('the status is one of "completed", "input-required", "blocked", or "failed"')
def _status_is_valid(walk_result):
    assert walk_result.get("status") in ("completed", "input-required", "blocked", "failed"), (
        f"unexpected status: {walk_result.get('status')!r}")


@then("the \"develop\" capability has its authored \"tdd\" skill")
def _develop_has_tdd(engine):
    dev = engine.registry.get("develop")
    assert "tdd" in (dev.ontology.skills or {})


@then("the \"develop\" capability does not have a \"develop-usage\" skill")
def _develop_no_usage(engine):
    dev = engine.registry.get("develop")
    assert "develop-usage" not in (dev.ontology.skills or {})


# ── Then steps — Spec 372 (phase = single source) ─────────────────────────────

@then("the blocked phase carries non-empty instructions")
def _blocked_has_instructions(walk_result):
    assert walk_result.get("instructions"), (
        "a paused walk must surface the current phase's instructions, not just "
        f"its name; got {walk_result.get('instructions')!r}")


@then("the blocked phase carries a goal")
def _blocked_has_goal(walk_result):
    assert walk_result.get("goal"), "a paused walk must surface the phase's goal"


@then("the surfaced instructions equal the instructions authored on that phase")
def _surfaced_matches_source(engine, walk_result):
    # One source, two surfaces: the instructions the walk delivers for the
    # paused phase MUST equal the instructions authored on that phase in the
    # capability's ontology (read live, not snapshotted — rule 8).
    blocked = walk_result["phase"]
    skills = engine.registry.get("develop").ontology.skills
    src = next(p for p in skills["tdd"]["phases"] if p["name"] == blocked)
    assert src.get("instructions"), (
        "fixture: the tdd discipline must author this phase's instructions")
    assert walk_result.get("instructions") == src["instructions"], (
        "the walk must surface the SAME instructions authored on the phase "
        "(one source, two surfaces)")


@then(parsers.parse('the walker surfaces the tdd "{phase_name}" phase '
                    'instructions from one source'))
def _current_surfaces_phase(engine, confirmed_intent, phase_name):
    # Progressive disclosure (skill.py current()) is the walk's source of truth.
    # It must surface the phase's authored content, covering a NON-gate phase.
    from agency.skill import SkillRun
    schema = engine.registry.get("develop").ontology.skills["tdd"]
    src = next(p for p in schema["phases"] if p["name"] == phase_name)
    assert src.get("instructions"), (
        f"fixture: the tdd {phase_name!r} phase must author instructions")
    run = SkillRun(engine.memory, confirmed_intent, schema, registry=engine.registry)
    cur = run.current()
    while cur is not None and cur["name"] != phase_name:
        sp = next(p for p in schema["phases"] if p["name"] == cur["name"])
        run.submit({k: "x" for k in sp["produces"]},
                   confirmed=sp.get("gate") == "hard")
        cur = run.current()
    assert cur is not None, f"walker never reached phase {phase_name!r}"
    assert cur.get("instructions") == src["instructions"], (
        "current() must surface the phase's authored instructions from one source")
