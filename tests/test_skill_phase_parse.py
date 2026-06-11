"""Spec 152 Slice 1 — typed Skill/Phase parse boundary.

Spec 003 (typed Skill/Phase parse/validate boundary) was Not Started, yet
the walkable-skill surface exploded — Specs 080/081 derive SkillDocs,
Specs 130/142/145 ship multi-phase walks, Spec 026 promotes Skills to
graph nodes. Every one parses phase dicts ad-hoc (see `agency/disclosure.py`
`render_phase` reading `phase.get("cue")` / `phase.get("gate")` / etc.).

Slice 1 ships the typed boundary:
- `Skill` + `Phase` dataclasses with a `variant` discriminator
  (`"hard_gate"` / `"soft_gate"` / `"computed_gate"` / `"verb_bound"` /
  `"step"`) covering every gate kind the live capability code already
  registers (Codex review on PR #127).
- `parse_skill(dict) -> ParseResult[Skill]` + `parse_phase(dict) ->
  ParseResult[Phase]` returning a typed result via the Spec 059 envelope.
- Typed failure codes on `Codes`: `SKILL_PARSE_INVALID`,
  `PHASE_MISSING_FIELD`, `PHASE_UNKNOWN_KIND`.
- Strict validation — non-list `phases` / `produces`, non-string
  `cue` / `reference` / `gate_verb`, non-int `index`, non-string
  produces/verbs elements, non-string gate — all fail with typed Codes
  rather than slipping past `or []` / `or ""` coercion (Codex review).

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


def test_soft_gate_phase_has_typed_variant():
    """Live skills in `subagent` + `skills` caps use `gate: "soft"` —
    Codex review: parser must accept it."""
    out = parse_phase({"name": "spec-review", "gate": "soft",
                       "produces": ["spec_passed"]})
    assert out.ok
    assert out.value.variant == "soft_gate"


def test_computed_gate_phase_has_typed_variant():
    """Music + prompt caps use `gate: "computed"` with `gate_verb` —
    Codex review: parser must accept the pair, reject computed-without-verb."""
    out = parse_phase({
        "name": "concept-gate", "gate": "computed",
        "gate_verb": "music.concept_gate",
        "produces": ["concept_ok"],
    })
    assert out.ok
    p = out.value
    assert p.variant == "computed_gate"
    assert p.gate_verb == "music.concept_gate"


def test_computed_gate_without_gate_verb_returns_typed_code():
    out = parse_phase({"name": "x", "gate": "computed"})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD
    assert "gate_verb" in out.message


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


def test_phase_carries_live_index_and_verbs():
    """`derive_usage_skill()` emits {index, name, produces, verbs} per phase
    — Codex review: parser must lift these to Phase fields, not drop them."""
    out = parse_phase({
        "index": 3, "name": "validate",
        "produces": ["lint_report"], "verbs": ["lint"], "gate": "soft",
    })
    assert out.ok
    p = out.value
    assert p.index == 3
    assert p.verbs == ("lint",)


def test_phase_immutable_dataclass():
    out = parse_phase({"name": "design", "produces": ["plan"]})
    p = out.value
    with pytest.raises(Exception):
        p.name = "changed"                                       # frozen


# ── parse_phase failure paths (strict validation per Codex review) ─────────
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
    """`gate` is constrained to documented values. Anything else is a typed
    `PHASE_UNKNOWN_KIND` so an LLM-driver that synthesizes a SkillDoc with
    a bogus gate is rejected at the boundary, never silently dispatched."""
    out = parse_phase({"name": "x", "gate": "bogus"})
    assert not out.ok
    assert out.code == Codes.PHASE_UNKNOWN_KIND


def test_phase_produces_non_list_returns_typed_code():
    """Codex review: `produces: ""` must fail, not coerce to []. The
    previous `or []` truthy fallback silently erased malformed produces."""
    out = parse_phase({"name": "x", "produces": ""})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD
    assert "produces" in out.message


def test_phase_produces_non_string_element_returns_typed_code():
    """Codex review: `produces: [1]` must fail, not pass as typed tuple
    despite the `tuple[str, ...]` declaration."""
    out = parse_phase({"name": "x", "produces": [1, 2]})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD


def test_phase_cue_non_string_returns_typed_code():
    """Codex review: `cue: ["text"]` must fail — disclosure.render_phase
    later concatenates cue as text, so a list/dict cue would produce a
    non-string prompt or fail later instead of being rejected here."""
    out = parse_phase({"name": "x", "cue": ["concat", "would", "fail"]})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD
    assert "cue" in out.message


def test_phase_reference_non_string_returns_typed_code():
    out = parse_phase({"name": "x", "reference": {"path": "ref.md"}})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD


def test_phase_index_non_int_returns_typed_code():
    out = parse_phase({"name": "x", "index": "3"})                 # string, not int
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD


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
    assert out.code == Codes.SKILL_PARSE_INVALID
    assert "phases[1]" in out.message


def test_parse_skill_missing_name_returns_typed_code():
    out = parse_skill({"phases": []})
    assert not out.ok
    assert out.code == Codes.SKILL_PARSE_INVALID


def test_parse_skill_non_list_phases_returns_typed_code():
    """Codex review: `phases: ""` previously parsed as an empty skill
    via `or []` truthy coercion. Must fail with SKILL_PARSE_INVALID."""
    out = parse_skill({"name": "x", "phases": ""})
    assert not out.ok
    assert out.code == Codes.SKILL_PARSE_INVALID
    assert "phases" in out.message


def test_parse_skill_preserves_top_level_kind():
    """`derive_usage_skill()` emits `kind: "usage"`; music/prompt caps emit
    `kind: "workflow"` / `"gate"`. Codex review: parser must preserve it
    so the round-trip stays lossless."""
    out = parse_skill({"name": "develop-usage", "kind": "usage", "phases": []})
    assert out.ok
    assert out.value.kind == "usage"


def test_parse_skill_round_trip_yields_same_dict_shape():
    """parse_clean(s).to_dict() == s — the round-trip invariant Slice 1
    asserts on a few hand-written specs; Slice 2 asserts it across the
    LIVE registry. Now covers `kind` + `index` + `verbs` + `gate_verb`."""
    s_in = {
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
    out = parse_skill(s_in)
    assert out.ok
    s_out = out.value.to_dict()
    assert s_out == s_in


# ── Codex round-2 review: live extras preservation + kind validation ──────
def test_skill_preserves_applies_when_via_extras():
    """`skills-triage` carries `applies_when` (agency/capabilities/skills.py:29).
    Codex review (round 2): parser must preserve it through the round trip
    so the matcher/projection downstream of Slice 2 can consume it."""
    s_in = {
        "name": "skills-triage",
        "kind": "triage",
        "applies_when": {"kind": "pattern", "text": "ship this skill"},
        "phases": [],
    }
    out = parse_skill(s_in)
    assert out.ok
    assert out.value.extras == {"applies_when": {"kind": "pattern",
                                                  "text": "ship this skill"}}
    # Round-trip preserves the field intact.
    assert out.value.to_dict() == s_in


def test_phase_preserves_inputs_via_extras():
    """Jules phases carry `inputs` (agency/capabilities/jules/skills.py:39).
    Parser must preserve it through the round trip."""
    s_in = {
        "name": "jules-dispatch",
        "phases": [
            {"index": 1, "name": "dispatch", "produces": ["session"],
             "inputs": ["source"]},
        ],
    }
    out = parse_skill(s_in)
    assert out.ok
    assert out.value.phases[0].extras == {"inputs": ["source"]}
    # Round-trip preserves the field.
    assert out.value.to_dict() == s_in


def test_phase_kind_hard_gate_requires_gate_hard():
    """Spec 003 `kind: "hard-gate"` shape. Codex review: my parser
    previously derived variant from gate only, so `{"kind": "hard-gate"}`
    without a `gate` parsed as a normal step — the silent-skip pattern.
    Now `kind` validates against the derived gate."""
    out = parse_phase({"name": "approve", "kind": "hard-gate"})
    assert not out.ok
    assert out.code == Codes.PHASE_UNKNOWN_KIND
    assert "hard" in out.message


def test_phase_kind_hard_gate_with_matching_gate_passes():
    out = parse_phase({"name": "approve", "kind": "hard-gate", "gate": "hard"})
    assert out.ok
    assert out.value.variant == "hard_gate"


def test_phase_unknown_kind_value_returns_typed_code():
    out = parse_phase({"name": "x", "kind": "bogus-kind"})
    assert not out.ok
    assert out.code == Codes.PHASE_UNKNOWN_KIND


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
