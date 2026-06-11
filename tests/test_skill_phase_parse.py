"""Spec 152 Slice 1 — typed Skill/Phase parse boundary.

Spec 003 (typed Skill/Phase parse/validate boundary) was Not Started, yet
the walkable-skill surface exploded — Specs 080/081 derive SkillDocs,
Specs 130/142/145 ship multi-phase walks, Spec 026 promotes Skills to
graph nodes. Every one parses phase dicts ad-hoc (see `agency/disclosure.py`
`render_phase` reading `phase.get("cue")` / `phase.get("gate")` / etc.).

Slice 1 ships the typed boundary:
- `Skill` + `Phase` dataclasses with a `variant` discriminator
  (`"hard_gate"` / `"verb_bound"` / `"step"`).
- `parse_skill(dict) -> ParseResult[Skill]` + `parse_phase(dict) ->
  ParseResult[Phase]` returning a typed result via the Spec 059 envelope.
- Typed failure codes on `Codes`: `SKILL_PARSE_INVALID`,
  `PHASE_MISSING_FIELD`, `PHASE_UNKNOWN_KIND`.

Slice 2+ — wiring `develop.skill_walk` through it; `_check_ad_hoc_phase_parse`
grep_ast monotone gate; live-tree round-trip invariant
(`parse_clean(live.skills) == live.skills`); LLM-driver SkillDoc validation.
"""
from __future__ import annotations

import pytest

from agency._skill_parse import (
    ParseResult,
    Phase,
    Skill,
    parse_phase,
    parse_skill,
)
from agency.toolresult import Codes


# ── Phase dataclass + variant discriminator ────────────────────────────────
def test_step_phase_is_default_variant():
    """No gate + no invoke → variant 'step'."""
    out = parse_phase({"name": "design", "produces": ["plan"]})
    assert out.ok and isinstance(out.value, Phase)
    p = out.value
    assert p.name == "design"
    assert p.variant == "step"
    assert p.produces == ("plan",)            # tuple — immutable


def test_hard_gate_phase_has_typed_variant():
    out = parse_phase({"name": "resolve", "gate": "hard",
                       "produces": ["addressed"]})
    assert out.ok
    assert out.value.variant == "hard_gate"
    assert out.value.gate == "hard"


def test_verb_bound_phase_has_typed_variant():
    out = parse_phase({"name": "lint",
                       "invoke": {"capability": "plugin",
                                  "verb": "lint_skill"}})
    assert out.ok
    p = out.value
    assert p.variant == "verb_bound"
    assert p.invoke == ("plugin", "lint_skill")


def test_phase_carries_optional_cue_and_reference():
    out = parse_phase({"name": "elicit", "cue": "Tell me one thing",
                       "reference": "see ref.md"})
    assert out.ok
    p = out.value
    assert p.cue == "Tell me one thing"
    assert p.reference == "see ref.md"


def test_phase_immutable_dataclass():
    out = parse_phase({"name": "design", "produces": ["plan"]})
    p = out.value
    with pytest.raises(Exception):
        p.name = "changed"                                       # frozen


# ── parse_phase failure paths ──────────────────────────────────────────────
def test_phase_missing_name_returns_typed_code():
    out = parse_phase({"produces": ["plan"]})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD
    assert "name" in out.message.lower()


def test_phase_invoke_missing_capability_returns_typed_code():
    out = parse_phase({"name": "x", "invoke": {"verb": "y"}})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD


def test_phase_unknown_gate_value_returns_typed_code():
    """`gate` is constrained — only "hard" today (Slice 2 may add "soft").
    Anything else is a typed `PHASE_UNKNOWN_KIND` so a Spec 147 LLM-driver
    that synthesizes a SkillDoc with a bogus gate value is rejected at the
    boundary, never silently dispatched."""
    out = parse_phase({"name": "x", "gate": "bogus"})
    assert not out.ok
    assert out.code == Codes.PHASE_UNKNOWN_KIND


# ── parse_skill + round-trip ───────────────────────────────────────────────
def test_parse_skill_returns_typed_skill_with_phases():
    out = parse_skill({
        "name": "develop",
        "phases": [
            {"name": "design", "produces": ["plan"]},
            {"name": "implement", "produces": ["code"]},
            {"name": "resolve", "gate": "hard", "produces": ["addressed"]},
        ],
    })
    assert out.ok
    skill = out.value
    assert isinstance(skill, Skill)
    assert skill.name == "develop"
    assert len(skill.phases) == 3
    variants = [p.variant for p in skill.phases]
    assert variants == ["step", "step", "hard_gate"]


def test_parse_skill_propagates_phase_failure():
    out = parse_skill({
        "name": "broken",
        "phases": [
            {"name": "good"},
            {"produces": ["x"]},                                  # missing `name`
        ],
    })
    assert not out.ok
    # Top-level Codes.SKILL_PARSE_INVALID is the wrapping code; the
    # message points at the offending phase index.
    assert out.code == Codes.SKILL_PARSE_INVALID
    assert "phases[1]" in out.message


def test_parse_skill_missing_name_returns_typed_code():
    out = parse_skill({"phases": []})
    assert not out.ok
    assert out.code == Codes.SKILL_PARSE_INVALID


def test_parse_skill_round_trip_yields_same_dict_shape():
    """parse_clean(s).to_dict() == s — the round-trip invariant Slice 1
    asserts on a few hand-written specs; Slice 2 asserts it across the
    LIVE registry (`live.skills` round-trips)."""
    s_in = {
        "name": "verify",
        "phases": [
            {"name": "design", "produces": ["plan"]},
            {"name": "implement", "produces": ["code"]},
        ],
    }
    out = parse_skill(s_in)
    assert out.ok
    s_out = out.value.to_dict()
    assert s_out == s_in


# ── Codes coverage ─────────────────────────────────────────────────────────
def test_skill_parse_codes_constants_land():
    """The Codes namespace gains the documented `SKILL_PARSE_*` + `PHASE_*`
    members the parse boundary returns (Spec 151 invariant b)."""
    assert Codes.SKILL_PARSE_INVALID == "skill_parse_invalid"
    assert Codes.PHASE_MISSING_FIELD == "phase_missing_field"
    assert Codes.PHASE_UNKNOWN_KIND == "phase_unknown_kind"


# ── ParseResult shape ──────────────────────────────────────────────────────
def test_parse_result_typed_envelope():
    out = parse_phase({"name": "x"})
    assert isinstance(out, ParseResult)
    assert out.ok is True and out.code == "" and out.message == ""

    bad = parse_phase({})
    assert bad.ok is False and bad.code != ""
