"""Acceptance — guided-discovery discipline skill registration (Spec 322 Slice 3).

Invariants (rule 8 — relationships, not snapshots):
- skill parses clean (no structural defects in the phase graph)
- kind="discipline" (overrides derived discover-usage)
- 7 phases, contiguous indices 1..7, each with ≥1 produces
- final phase gate="computed", gate_verb="clarity_gate"
- registered in the engine ontology so the walker can find it
"""
from __future__ import annotations

from pytest_bdd import given, scenarios, then, when

from agency._skill_parse import parse_skill
from agency.capabilities.discover.ontology import GUIDED_DISCOVERY_SKILL

scenarios("features/guided_discovery_skill.feature")


# ── fixtures ─────────────────────────────────────────────────────────────────

@when("I load the guided-discovery skill from the discover ontology",
      target_fixture="skill_result")
def _load_skill():
    return parse_skill(GUIDED_DISCOVERY_SKILL)


# ── parse correctness ─────────────────────────────────────────────────────────

@then("parse_skill returns success")
def _parses_ok(skill_result):
    assert skill_result.ok, f"parse_skill failed: {skill_result.message}"


@then('the skill kind is "discipline"')
def _is_discipline(skill_result):
    assert skill_result.ok, skill_result.message
    assert skill_result.value.kind == "discipline", skill_result.value.kind


# ── phase invariants ──────────────────────────────────────────────────────────

@then("the skill has exactly 7 phases")
def _seven_phases(skill_result):
    assert skill_result.ok, skill_result.message
    n = len(skill_result.value.phases)
    assert n == 7, f"expected 7 phases, got {n}"


@then("every phase declares at least one produces item")
def _all_phases_have_produces(skill_result):
    assert skill_result.ok, skill_result.message
    for ph in skill_result.value.phases:
        assert ph.produces, (
            f"phase '{ph.name}' has no produces — the walker reads it "
            "unconditionally (Spec 018)"
        )


@then("phase indices are 1 through 7 in order")
def _contiguous_indices(skill_result):
    assert skill_result.ok, skill_result.message
    indices = [ph.index for ph in skill_result.value.phases]
    assert indices == list(range(1, 8)), (
        f"expected contiguous 1..7, got {indices}"
    )


# ── gate invariants (the Spec 322 Slice 3 deliverable) ────────────────────────

@then('the last phase name is "decide"')
def _last_phase_name(skill_result):
    assert skill_result.ok, skill_result.message
    last = skill_result.value.phases[-1]
    assert last.name == "decide", f"last phase is {last.name!r}, expected 'decide'"


@then('the last phase gate is "computed"')
def _last_phase_gate(skill_result):
    assert skill_result.ok, skill_result.message
    last = skill_result.value.phases[-1]
    assert last.gate == "computed", (
        f"last phase gate is {last.gate!r}, expected 'computed'"
    )


@then('the last phase gate_verb is "clarity_gate"')
def _last_phase_gate_verb(skill_result):
    assert skill_result.ok, skill_result.message
    last = skill_result.value.phases[-1]
    assert last.gate_verb == "clarity_gate", (
        f"last phase gate_verb is {last.gate_verb!r}, expected 'clarity_gate'"
    )


# ── engine registration ───────────────────────────────────────────────────────

@then('"guided-discovery" is registered in the engine ontology skills')
def _registered_in_engine(engine):
    skills = engine.ontology.skills
    assert "guided-discovery" in skills, (
        f"'guided-discovery' not in ontology.skills (found: {sorted(skills)})"
    )
    registered = skills["guided-discovery"]
    assert registered.get("name") == "guided-discovery", registered
    assert registered.get("kind") == "discipline", registered
