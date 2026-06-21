"""Acceptance — Skill schema v2 (Spec 371): the layered, type-classified
Phase + Skill data model.

The v2 schema is what 372–378 consume. This suite pins:
  - Phase inline content (goal/instructions/example/done_when/freedom) +
    lossless round-trip (A1/A2/R8/R9).
  - Skill type classification (R15) with a per-type required core (layered
    floor) — the malformed-skill failure path.
  - Back-compat: a legacy skill (no `type`) parses exactly as before, and
    every live ontology skill stays clean (the iron invariant).
  - R1–A7 rule → schema-field coverage, and the published JSON schemas.
"""
from __future__ import annotations

import json
from pathlib import Path

from pytest_bdd import parsers, scenarios, then, when

scenarios("features/skill_schema_v2.feature")

_SCHEMA_DIR = (
    Path(__file__).resolve().parents[2]
    / "agency" / "capabilities" / "plugin" / "schemas"
)


# ── When steps — Phase content fields ─────────────────────────────────────────

@when("I parse a phase with goal, instructions, example, done_when and freedom",
      target_fixture="parse_result")
def _parse_phase_v2_content():
    from agency._skill_parse import parse_phase
    return parse_phase({
        "name": "design",
        "produces": ["plan"],
        "goal": "produce a one-page implementation plan",
        "instructions": "1. Read the spec.\n2. List the slices.\n3. Write the plan.",
        "example": "## Plan\n- slice 1: schema\n- slice 2: loader",
        "done_when": "the plan names every slice with a test",
        "freedom": "medium",
    })


@when(parsers.parse('I parse a phase with freedom "{level}"'),
      target_fixture="parse_result")
def _parse_phase_bad_freedom(level):
    from agency._skill_parse import parse_phase
    return parse_phase({"name": "x", "produces": ["r"], "freedom": level})


# ── When steps — Skill type classification ────────────────────────────────────

@when("I parse a discipline skill with description and common_mistakes",
      target_fixture="parse_result")
def _parse_discipline_ok():
    from agency._skill_parse import parse_skill
    return parse_skill({
        "name": "frugal", "kind": "discipline", "type": "discipline",
        "description": "Use when adding code — reach for the leanest path first.",
        "common_mistakes": [
            {"symptom": "installs a library for a one-liner",
             "counter": "check the stdlib and native platform first"},
        ],
    })


@when("I parse a discipline skill with no common_mistakes",
      target_fixture="parse_result")
def _parse_discipline_missing():
    from agency._skill_parse import parse_skill
    return parse_skill({
        "name": "frugal", "kind": "discipline", "type": "discipline",
        "description": "Use when adding code — reach for the leanest path first.",
    })


@when("I parse a technique skill with no phases", target_fixture="parse_result")
def _parse_technique_missing():
    from agency._skill_parse import parse_skill
    return parse_skill({
        "name": "implement", "kind": "workflow", "type": "technique",
        "description": "Use when turning a spec into code via TDD.",
    })


@when("I parse a reference skill with no references", target_fixture="parse_result")
def _parse_reference_missing():
    from agency._skill_parse import parse_skill
    return parse_skill({
        "name": "codegraph", "kind": "reference", "type": "reference",
        "description": "Use when navigating code — symbols, calls, blast radius.",
    })


@when("I parse a pattern skill with no overview", target_fixture="parse_result")
def _parse_pattern_missing():
    from agency._skill_parse import parse_skill
    return parse_skill({
        "name": "dispatch-decision", "kind": "conceptualizer", "type": "pattern",
        "description": "Use when deciding whether to dispatch or run inline.",
    })


@when(parsers.parse('I parse a skill with type "{stype}"'),
      target_fixture="parse_result")
def _parse_bad_type(stype):
    from agency._skill_parse import parse_skill
    return parse_skill({
        "name": "x", "kind": "workflow", "type": stype,
        "description": "Use when doing the thing.",
    })


@when(parsers.parse('I parse a skill with owner "{owner}"'),
      target_fixture="parse_result")
def _parse_bad_owner(owner):
    from agency._skill_parse import parse_skill
    return parse_skill({
        "name": "x", "kind": "workflow", "type": "capability", "owner": owner,
        "description": "Use when doing the thing.",
    })


@when("I parse a full capability skill with all v2 fields",
      target_fixture="parse_result")
def _parse_full_capability():
    from agency._skill_parse import parse_skill
    return parse_skill({
        "name": "develop", "kind": "discipline", "type": "capability",
        "owner": "capability",
        "description": "Use when planning, writing, testing or reviewing code in agency.",
        "overview": "develop is the SDLC capability — brainstorm → spec → implement → test.",
        "when_to_use": "starting any code change, spec, or review",
        "when_not": "pure prose edits with no code (use document.*)",
        "references": [
            {"path": "docs/guide/develop.md", "title": "The develop guide"},
            {"path": "Plan/152-typed-parse/spec.md"},
        ],
        "common_mistakes": [
            {"symptom": "grepping when codegraph exists",
             "counter": "reach for codegraph_explore first"},
        ],
        "examples": [
            {"input": "develop.test('frugal')", "output": "the frugal slice runs in ~6s"},
        ],
        "eval_scenarios": [
            {"name": "spec→code", "expect": "a passing acceptance test"},
        ],
        "source_stamp": "sha256:abc123",
        "phases": [
            {"index": 1, "name": "design", "produces": ["plan"],
             "goal": "one-page plan", "instructions": "list the slices",
             "freedom": "high"},
        ],
    })


@when("I parse a legacy skill with only name kind and phases",
      target_fixture="parse_result")
def _parse_legacy():
    from agency._skill_parse import parse_skill
    return parse_skill({
        "name": "develop", "kind": "discipline",
        "phases": [{"name": "design", "produces": ["plan"]}],
    })


# ── Then steps — phase ────────────────────────────────────────────────────────

@then("the v2 phase parse succeeds")
def _v2_phase_ok(parse_result):
    assert parse_result.ok, f"parse failed: {parse_result.message}"


@then(parsers.parse('the v2 phase parse fails with code "{code}" mentioning "{term}"'))
def _v2_phase_fails(parse_result, code, term):
    assert not parse_result.ok
    assert parse_result.code == code, (
        f"expected code={code!r}, got {parse_result.code!r}")
    assert term in parse_result.message, (
        f"expected {term!r} in message; got {parse_result.message!r}")


@then("the phase round-trips its instructions and freedom")
def _phase_roundtrip(parse_result):
    assert parse_result.ok
    d = parse_result.value.to_dict()
    assert d["instructions"].startswith("1. Read the spec.")
    assert d["goal"] == "produce a one-page implementation plan"
    assert d["example"].startswith("## Plan")
    assert d["done_when"] == "the plan names every slice with a test"
    assert d["freedom"] == "medium"


# ── Then steps — skill ────────────────────────────────────────────────────────

@then(parsers.parse('the v2 skill parse succeeds with type "{stype}"'))
def _v2_skill_ok_type(parse_result, stype):
    assert parse_result.ok, f"parse failed: {parse_result.message}"
    assert parse_result.value.type == stype


@then("the v2 skill parse succeeds with no type")
def _v2_skill_ok_no_type(parse_result):
    assert parse_result.ok, f"parse failed: {parse_result.message}"
    assert parse_result.value.type == ""


@then(parsers.parse('the v2 skill parse fails with code "{code}" mentioning "{term}"'))
def _v2_skill_fails(parse_result, code, term):
    assert not parse_result.ok
    assert parse_result.code == code, (
        f"expected code={code!r}, got {parse_result.code!r}")
    assert term in parse_result.message, (
        f"expected {term!r} in message; got {parse_result.message!r}")


@then("the skill round-trips description, overview, references and examples")
def _skill_roundtrip(parse_result):
    assert parse_result.ok
    d = parse_result.value.to_dict()
    assert d["description"].startswith("Use when planning")
    assert d["overview"].startswith("develop is the SDLC capability")
    assert d["owner"] == "capability"
    assert d["references"][0] == {
        "path": "docs/guide/develop.md", "title": "The develop guide"}
    assert d["references"][1] == {"path": "Plan/152-typed-parse/spec.md"}
    assert d["common_mistakes"][0]["counter"] == "reach for codegraph_explore first"
    assert d["examples"][0]["input"] == "develop.test('frugal')"
    assert d["eval_scenarios"][0]["name"] == "spec→code"
    assert d["source_stamp"] == "sha256:abc123"
    # the phase's inline content survives the skill round-trip too
    assert d["phases"][0]["instructions"] == "list the slices"
    assert d["phases"][0]["freedom"] == "high"


# ── Then steps — live invariant ───────────────────────────────────────────────

@then("every live skill parses clean under the v2 schema")
def _live_v2_clean(engine):
    from agency._skill_parse import parse_skill
    skills = getattr(engine.ontology, "skills", {}) or {}
    assert skills, "live ontology should expose registered skills"
    failures = []
    for name, sk in skills.items():
        res = parse_skill(sk)
        if not res.ok:
            failures.append((name, res.code, res.message[:200]))
    assert failures == [], (
        "live skills failed v2 parse_skill:\n"
        + "\n".join(f"  {n}  {c}  {m}" for n, c, m in failures))


# ── Then steps — R1–A7 coverage + JSON schemas ────────────────────────────────

# Each best-practices rule that the data model must EXPRESS maps to a concrete
# Phase/Skill field (Spec 371 acceptance: "the schema can express each R1–A7
# field"). Computed against the live dataclasses — no frozen snapshot.
_RULE_TO_FIELD = {
    "R1-description-when-not-what": ("skill", "description"),
    "R8-degrees-of-freedom": ("phase", "freedom"),
    "R9-one-example": ("skill", "examples"),
    "R14-eval-scenarios": ("skill", "eval_scenarios"),
    "R15-type": ("skill", "type"),
    "A1-self-contained-instructions": ("phase", "instructions"),
    "A2-phase-goal": ("phase", "goal"),
    "A2-phase-done-when": ("phase", "done_when"),
    "A4-source-stamp": ("skill", "source_stamp"),
    "A6-owner": ("skill", "owner"),
    "discipline-rationalization-table": ("skill", "common_mistakes"),
    "progressive-disclosure-references": ("skill", "references"),
    "skill-overview": ("skill", "overview"),
    "skill-when-not": ("skill", "when_not"),
}


@then("every best-practices rule maps to a schema field")
def _rule_field_coverage():
    import dataclasses

    from agency._skill_parse import Phase, Skill
    phase_fields = {f.name for f in dataclasses.fields(Phase)}
    skill_fields = {f.name for f in dataclasses.fields(Skill)}
    missing = []
    for rule, (owner, field) in _RULE_TO_FIELD.items():
        present = field in (phase_fields if owner == "phase" else skill_fields)
        if not present:
            missing.append(f"{rule} → {owner}.{field}")
    assert not missing, "rules with no schema field: " + ", ".join(missing)


@then("the phase JSON schema declares the inline content fields")
def _phase_schema_declares():
    schema = json.loads((_SCHEMA_DIR / "phase-schema.json").read_text())
    props = schema.get("properties", {})
    for field in ("goal", "instructions", "example", "done_when", "freedom"):
        assert field in props, f"phase-schema.json missing property {field!r}"


@then("the skill JSON schema declares every skill type and the v2 fields")
def _skill_schema_declares():
    from agency._skill_parse import _SKILL_TYPES
    schema = json.loads((_SCHEMA_DIR / "skill-schema.json").read_text())
    props = schema.get("properties", {})
    for field in ("type", "owner", "description", "overview", "references",
                  "common_mistakes", "examples", "eval_scenarios", "source_stamp"):
        assert field in props, f"skill-schema.json missing property {field!r}"
    declared_types = set(props["type"].get("enum", []))
    assert declared_types == set(_SKILL_TYPES), (
        f"skill-schema.json type enum {declared_types} != live {set(_SKILL_TYPES)}")
