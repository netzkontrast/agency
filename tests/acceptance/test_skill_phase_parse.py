"""Acceptance — Skill/Phase parse boundary behaviour.

Converted from:
  tests/test_skill_phase_parse.py  (Spec 152 — typed parse_skill / parse_phase)

Dropped as implementation/structural (not observable behaviour):
  test_skill_walk_slices.py — render_phase / render_verb output format tests
    (T1/T2/T3 depth slices, snippet call_tool syntax, fallback text) are
    internal disclosure-helper details. A client observes skill_walk output,
    not the intermediate rendering strings. The one observable behaviour
    there (a verb-bound phase executes its verb) is already in skill_walk.feature.
  Codes constant tests (Codes.SKILL_PARSE_INVALID == "skill_parse_invalid" etc.)
    — these pin enum string literals, which are implementation choices.
  ParseResult field presence tests — the data-class field set is structural;
    what matters is the observable ok/code/message semantics on parse failures,
    which is covered by the scenario group below.

The live-invariant scenario (every live ontology skill parses clean) IS
  observable behaviour — a new malformed skill would break walking; kept.
SkillRun construction scenarios ARE observable — the constructor raises for
  invalid schemas, which the walker surfaces as a failed contract.
"""
from __future__ import annotations

import tempfile

from pytest_bdd import parsers, scenarios, then, when

scenarios("features/skill_phase_parse.feature")


# ── helpers ──────────────────────────────────────────────────────────────────

def _phase(parse_result):
    """Unwrap a ParseResult to the Phase value (caller asserts ok first)."""
    return parse_result.value


# ── When steps — parse_phase ──────────────────────────────────────────────────

@when("I parse a phase with name \"design\" and produces [\"plan\"]",
      target_fixture="parse_result")
def _parse_step_phase():
    from agency._skill_parse import parse_phase
    return parse_phase({"name": "design", "produces": ["plan"]})


@when("I parse a phase with gate \"hard\"", target_fixture="parse_result")
def _parse_hard():
    from agency._skill_parse import parse_phase
    return parse_phase({"name": "resolve", "gate": "hard", "produces": ["addressed"]})


@when("I parse a phase with gate \"soft\"", target_fixture="parse_result")
def _parse_soft():
    from agency._skill_parse import parse_phase
    return parse_phase({"name": "spec-review", "gate": "soft",
                        "produces": ["spec_passed"]})


@when("I parse a phase with gate \"computed\" and gate_verb \"music.verify_gate\"",
      target_fixture="parse_result")
def _parse_computed():
    from agency._skill_parse import parse_phase
    return parse_phase({
        "name": "concept-gate", "gate": "computed",
        "gate_verb": "music.verify_gate",
        "produces": ["concept_ok"],
    })


@when("I parse a phase with gate \"computed\" but no gate_verb",
      target_fixture="parse_result")
def _parse_computed_no_verb():
    from agency._skill_parse import parse_phase
    return parse_phase({"name": "x", "gate": "computed", "produces": ["r"]})


@when("I parse a phase with invoke capability \"plugin\" verb \"lint_skill\"",
      target_fixture="parse_result")
def _parse_verb_bound():
    from agency._skill_parse import parse_phase
    return parse_phase({"name": "lint", "produces": ["lint_report"],
                        "invoke": {"capability": "plugin", "verb": "lint_skill"}})


@when("I parse a phase dict that has no \"name\" key", target_fixture="parse_result")
def _parse_no_name():
    from agency._skill_parse import parse_phase
    return parse_phase({"produces": ["plan"]})


@when("I parse a phase with gate \"bogus\"", target_fixture="parse_result")
def _parse_bogus_gate():
    from agency._skill_parse import parse_phase
    return parse_phase({"name": "x", "gate": "bogus"})


@when("I parse a phase with produces set to an empty string",
      target_fixture="parse_result")
def _parse_produces_string():
    from agency._skill_parse import parse_phase
    return parse_phase({"name": "x", "produces": ""})


@when("I parse a phase with produces [1, 2]", target_fixture="parse_result")
def _parse_produces_int():
    from agency._skill_parse import parse_phase
    return parse_phase({"name": "x", "produces": [1, 2]})


@when("I parse a phase with both invoke and gate \"hard\"",
      target_fixture="parse_result")
def _parse_invoke_and_hard_gate():
    from agency._skill_parse import parse_phase
    return parse_phase({
        "name": "lint", "produces": ["lint_report"],
        "gate": "hard",
        "invoke": {"capability": "plugin", "verb": "lint_skill"},
    })


@when("I parse a verb-bound phase with two produces entries",
      target_fixture="parse_result")
def _parse_two_produces_invoke():
    from agency._skill_parse import parse_phase
    return parse_phase({
        "name": "lint", "produces": ["a", "b"],
        "invoke": {"capability": "plugin", "verb": "lint_skill"},
    })


# ── When steps — parse_skill ──────────────────────────────────────────────────

@when("I parse a skill with name \"develop\" and three phases including a hard gate",
      target_fixture="parse_result")
def _parse_skill_three_phases():
    from agency._skill_parse import parse_skill
    return parse_skill({
        "name": "develop", "kind": "discipline",
        "phases": [
            {"name": "design", "produces": ["plan"]},
            {"name": "implement", "produces": ["code"]},
            {"name": "resolve", "gate": "hard", "produces": ["addressed"]},
        ],
    })


@when("I parse a skill whose second phase is missing a \"name\"",
      target_fixture="parse_result")
def _parse_skill_bad_phase():
    from agency._skill_parse import parse_skill
    return parse_skill({
        "name": "broken", "kind": "discipline",
        "phases": [
            {"name": "good", "produces": ["ok"]},
            {"produces": ["x"]},
        ],
    })


@when("I parse a skill dict that has no \"name\" key", target_fixture="parse_result")
def _parse_skill_no_name():
    from agency._skill_parse import parse_skill
    return parse_skill({"phases": []})


@when("I parse a skill with phases set to an empty string",
      target_fixture="parse_result")
def _parse_skill_phases_string():
    from agency._skill_parse import parse_skill
    return parse_skill({"name": "x", "phases": ""})


@when("I parse a skill with only name and phases but no kind",
      target_fixture="parse_result")
def _parse_skill_no_kind():
    from agency._skill_parse import parse_skill
    return parse_skill({"name": "x", "phases": [
        {"name": "p", "produces": ["r"]}]})


@when("I parse a skill with kind \"usage\"", target_fixture="parse_result")
def _parse_skill_kind():
    from agency._skill_parse import parse_skill
    return parse_skill({"name": "develop-usage", "kind": "usage", "phases": []})


@when("I parse a multi-phase skill with index, verbs, computed gate, and hard gate phases",
      target_fixture="parse_result")
def _parse_skill_complex():
    from agency._skill_parse import parse_skill
    return parse_skill({
        "name": "pre-generation",
        "kind": "gate",
        "phases": [
            {"index": 1, "name": "research-cover", "produces": ["covered"]},
            {"index": 2, "name": "verify-sources",
             "produces": ["verified"], "verbs": ["music.verify_sources"],
             "gate": "computed", "gate_verb": "music.verify_gate"},
            {"index": 3, "name": "approve",
             "produces": ["approved"], "gate": "hard"},
        ],
    })


@when("I parse a skill whose phases have indices [1, 3] skipping 2",
      target_fixture="parse_result")
def _parse_skill_noncontiguous():
    from agency._skill_parse import parse_skill
    return parse_skill({
        "name": "x", "kind": "discipline",
        "phases": [
            {"index": 1, "name": "a", "produces": ["x"]},
            {"index": 3, "name": "b", "produces": ["y"]},
        ],
    })


# ── When steps — live + SkillRun ──────────────────────────────────────────────

@when("I construct a SkillRun with a phase missing its name field",
      target_fixture="skillrun_error")
def _skillrun_bad():
    from agency.engine import Engine
    from agency.skill import SkillRun
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = e.intent.capture("p", "d", "a")
    e.intent.confirm(iid)
    bad = {"name": "x", "kind": "workflow", "phases": [{}]}
    try:
        SkillRun(e.memory, iid, bad)
        return None
    except ValueError as err:
        return err
    finally:
        e.memory.close()


@when("I construct a SkillRun with a valid one-phase schema",
      target_fixture="skillrun_result")
def _skillrun_good():
    from agency.engine import Engine
    from agency.skill import SkillRun
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = e.intent.capture("p", "d", "a")
    e.intent.confirm(iid)
    schema = {"name": "tiny", "kind": "workflow",
              "phases": [{"index": 1, "name": "p1", "produces": ["r"]}]}
    run = SkillRun(e.memory, iid, schema)
    current = run.current()
    e.memory.close()
    return current


# ── Then steps — Phase variant ────────────────────────────────────────────────

@then(parsers.parse('the parse succeeds with variant "{variant}"'))
def _succeeds_variant(parse_result, variant):
    assert parse_result.ok, f"parse failed: {parse_result.message}"
    assert parse_result.value.variant == variant


@then("the parse succeeds with 3 phases")
def _three_phases(parse_result):
    assert parse_result.ok
    assert len(parse_result.value.phases) == 3


@then("the phase variants are [\"step\", \"step\", \"hard_gate\"]")
def _phase_variants(parse_result):
    variants = [p.variant for p in parse_result.value.phases]
    assert variants == ["step", "step", "hard_gate"]


@then(parsers.parse('the parse fails with code "{code}" mentioning "{term}"'))
def _fails_code_term(parse_result, code, term):
    assert not parse_result.ok
    assert parse_result.code == code, f"expected code={code!r}, got {parse_result.code!r}"
    assert term in parse_result.message, (
        f"expected {term!r} in message; got {parse_result.message!r}")


@then(parsers.parse('the parse fails with code "{code}"'))
def _fails_code(parse_result, code):
    assert not parse_result.ok
    assert parse_result.code == code, f"expected code={code!r}, got {parse_result.code!r}"


@then("the round-trip to_dict preserves the kind")
def _roundtrip_kind(parse_result):
    assert parse_result.ok
    d = parse_result.value.to_dict()
    assert d["kind"] == "usage"


@then("the round-trip to_dict equals the input dict")
def _roundtrip_complex(parse_result):
    assert parse_result.ok
    expected = {
        "name": "pre-generation",
        "kind": "gate",
        "phases": [
            {"index": 1, "name": "research-cover", "produces": ["covered"]},
            {"index": 2, "name": "verify-sources",
             "produces": ["verified"], "verbs": ["music.verify_sources"],
             "gate": "computed", "gate_verb": "music.verify_gate"},
            {"index": 3, "name": "approve",
             "produces": ["approved"], "gate": "hard"},
        ],
    }
    assert parse_result.value.to_dict() == expected


# ── Then steps — live invariant ───────────────────────────────────────────────

@then("every skill in the live ontology passes parse_skill with no failures")
def _live_skills_parse_clean(engine):
    from agency._skill_parse import parse_skill
    skills = getattr(engine.ontology, "skills", {}) or {}
    assert skills, "live ontology should expose registered skills"
    failures = []
    for name, sk in skills.items():
        res = parse_skill(sk)
        if not res.ok:
            failures.append((name, res.code, res.message[:200]))
    assert failures == [], (
        "live skills failed parse_skill:\n"
        + "\n".join(f"  {n}  {c}  {m}" for n, c, m in failures))


# ── Then steps — SkillRun ─────────────────────────────────────────────────────

@then("a ValueError is raised with a typed code in the message")
def _skillrun_value_error(skillrun_error):
    assert isinstance(skillrun_error, ValueError), (
        f"expected ValueError; got {skillrun_error!r}")
    from agency.toolresult import Codes
    msg = str(skillrun_error)
    assert any(code in msg for code in
               (Codes.SKILL_PARSE_INVALID, Codes.PHASE_MISSING_FIELD)), (
        f"typed code not in error message: {msg!r}")


@then("the current phase name is returned without error")
def _skillrun_ok(skillrun_result):
    assert skillrun_result["name"] == "p1"
