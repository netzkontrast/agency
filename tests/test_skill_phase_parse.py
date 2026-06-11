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
    out = parse_phase({"name": "x", "gate": "computed", "produces": ["r"]})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD
    assert "gate_verb" in out.message


def test_verb_bound_phase_has_typed_variant():
    out = parse_phase({"name": "lint", "produces": ["lint_report"],
                       "invoke": {"capability": "plugin",
                                  "verb": "lint_skill"}})
    assert out.ok
    p = out.value
    assert p.variant == "verb_bound"
    assert p.invoke == ("plugin", "lint_skill")


def test_phase_carries_optional_cue_and_reference():
    out = parse_phase({"name": "elicit", "produces": ["answer"],
                       "cue": "Tell me one thing",
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
        "name": "develop", "kind": "discipline",
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
        "name": "broken", "kind": "discipline",
        "phases": [
            {"name": "good", "produces": ["ok"]},
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


def test_phase_lifts_and_validates_inputs():
    """Jules phases carry `inputs` (agency/capabilities/jules/skills.py:39);
    SkillRun.submit() iterates `p.get("inputs", [])` to build kwargs.
    Codex review (round 5): lift + validate as a list of strings
    (matches produces/verbs treatment) rather than slipping it through
    extras unchecked."""
    s_in = {
        "name": "jules-dispatch", "kind": "discipline",
        "phases": [
            {"index": 1, "name": "dispatch", "produces": ["session"],
             "inputs": ["source"]},
        ],
    }
    out = parse_skill(s_in)
    assert out.ok
    p = out.value.phases[0]
    assert p.inputs == ("source",)                                 # tuple — typed first-class
    # Round-trip preserves the field.
    assert out.value.to_dict() == s_in


def test_phase_inputs_non_list_returns_typed_code():
    """Codex review: `inputs: "source"` would split into characters if
    silently accepted; reject at the boundary."""
    out = parse_phase({"name": "x", "produces": ["r"], "inputs": "source"})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD
    assert "inputs" in out.message


def test_phase_missing_produces_returns_typed_code():
    """Codex review: the walker reads `p["produces"]` unconditionally.
    A phase that omits produces would raise KeyError on the first
    disclosure step; reject at the parse boundary instead."""
    out = parse_phase({"name": "design"})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD
    assert "produces" in out.message


def test_phase_kind_hard_gate_alone_implies_gate_hard():
    """Codex review (round 5): Spec 003 `kind: "hard-gate"` shape (no
    redundant `gate` field) MUST work — the kind implies the gate. The
    SkillDoc form `{"kind": "hard-gate", "predicate": "tests_green"}`
    is the documented spec.md example."""
    out = parse_phase({"name": "approve", "kind": "hard-gate",
                       "produces": ["approved"],
                       "predicate": "tests_green"})
    assert out.ok
    assert out.value.variant == "hard_gate"                        # derived from kind
    # Codex review round-6: gate stays at source value (empty) so the
    # round-trip doesn't synthesize a `gate: "hard"` field.
    assert out.value.gate == ""


def test_phase_kind_hard_gate_with_matching_gate_passes():
    out = parse_phase({"name": "approve", "kind": "hard-gate", "gate": "hard",
                       "produces": ["approved"],
                       "predicate": "tests_green"})
    assert out.ok
    assert out.value.variant == "hard_gate"


def test_phase_unknown_kind_value_returns_typed_code():
    out = parse_phase({"name": "x", "kind": "bogus-kind"})
    assert not out.ok
    assert out.code == Codes.PHASE_UNKNOWN_KIND


# ── Codex round-3 review fixes ────────────────────────────────────────────
def test_skill_falsy_non_string_kind_returns_typed_code():
    """Codex review: `kind: 0` / `kind: False` previously slipped past
    `if kind and not isinstance(kind, str)` (the `and kind` short-circuit
    skipped validation for falsy values), then `kind or ""` erased it.
    Must fail fast with SKILL_PARSE_INVALID."""
    for falsy in (0, False, [], {}):
        out = parse_skill({"name": "x", "kind": falsy, "phases": []})
        assert not out.ok, f"falsy kind {falsy!r} unexpectedly passed"
        assert out.code == Codes.SKILL_PARSE_INVALID


def test_phase_kind_preserved_through_round_trip():
    """Codex review: phase-level `kind` parsed successfully but Phase
    didn't store it, so to_dict() dropped it from valid SkillDocs using
    the Spec 003 documented shape."""
    s_in = {
        "name": "approve-flow", "kind": "discipline",
        "phases": [
            {"name": "approve", "kind": "hard-gate", "gate": "hard",
             "predicate": "tests_green", "produces": ["ok"]},
        ],
    }
    out = parse_skill(s_in)
    assert out.ok
    assert out.value.phases[0].kind == "hard-gate"
    assert out.value.to_dict() == s_in                              # round-trip


def test_verb_bound_phase_without_produces_returns_typed_code():
    """Codex review: `invoke` set + empty `produces` → walker stores at
    `p["produces"][0]` and crashes. Must fail fast at the parse boundary."""
    out = parse_phase({
        "name": "lint",
        "invoke": {"capability": "plugin", "verb": "lint_skill"},
        # no produces
    })
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD
    assert "produces" in out.message


def test_verb_bound_phase_with_empty_produces_returns_typed_code():
    out = parse_phase({
        "name": "lint",
        "produces": [],                                            # empty list
        "invoke": {"capability": "plugin", "verb": "lint_skill"},
    })
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD


def test_phase_kind_verb_bound_without_invoke_returns_typed_code():
    """Codex review: `kind: "verb-bound"` MUST come paired with an `invoke`
    block. Without it the variant defaulted to "step" and the phase was
    silently walked as a step instead of failing fast."""
    out = parse_phase({
        "name": "delegate", "kind": "verb-bound",
        "produces": ["result"],                                    # required
        # no invoke
    })
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD
    assert "invoke" in out.message


# ── Codex round-4 review fixes ────────────────────────────────────────────
def test_hard_gate_kind_without_predicate_returns_typed_code():
    """spec.md worked failure case: `kind="hard-gate"` without a
    `predicate` must fail at the parse boundary (otherwise Slice 2
    routes a typed hard gate with no predicate for the walker to
    enforce)."""
    out = parse_phase({"name": "approve", "kind": "hard-gate", "gate": "hard",
                       "produces": ["approved"]})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD
    assert "predicate" in out.message


def test_verb_bound_phase_with_gate_computed_skips_gate_verb():
    """Codex review: when both `invoke` and `gate: "computed"` are
    present, `_derive_variant` returns `verb_bound` (invoke wins). The
    pre-derive gate_verb check must not reject — the invoked verb's
    own gate semantics take over."""
    out = parse_phase({
        "name": "delegate-gate",
        "produces": ["result"],
        "gate": "computed",                                        # would normally need gate_verb
        "invoke": {"capability": "music", "verb": "verify_gate"},
        # no gate_verb — the verb_bound variant doesn't need it
    })
    assert out.ok
    assert out.value.variant == "verb_bound"


def test_phase_kind_hard_gate_with_invoke_returns_typed_code():
    """Codex review: `kind: "hard-gate"` + `invoke: ...` derives
    variant `verb_bound` (invoke wins), so the declared kind
    contradicts how the phase actually walks. Must fail fast instead
    of executing the verb under a hard-gate label."""
    out = parse_phase({
        "name": "lint", "kind": "hard-gate", "gate": "hard",
        "produces": ["lint_report"],
        "invoke": {"capability": "plugin", "verb": "lint_skill"},
    })
    assert not out.ok
    assert out.code == Codes.PHASE_UNKNOWN_KIND
    assert "verb_bound" in out.message


# ── Codex round-6 review fixes ────────────────────────────────────────────
def test_kind_only_hard_gate_round_trips_without_synthesizing_gate():
    """Codex review: `{"kind": "hard-gate", "predicate": "x"}` without an
    explicit `gate` field must round-trip cleanly — `to_dict()` must NOT
    synthesize a `gate: "hard"` key the source dict didn't have."""
    p_in = {"name": "approve", "kind": "hard-gate",
            "produces": ["ok"], "predicate": "tests_green"}
    out = parse_phase(p_in)
    assert out.ok
    p_out = out.value.to_dict()
    assert p_out == p_in                                           # round-trip
    assert "gate" not in p_out                                     # not synthesized


def test_skill_missing_kind_returns_typed_code():
    """Codex review: walker reads `schema["kind"]` unconditionally; a
    skill without `kind` must fail at the parse boundary."""
    out = parse_skill({"name": "x", "phases": [
        {"name": "p", "produces": ["r"]}]})
    assert not out.ok
    assert out.code == Codes.SKILL_PARSE_INVALID
    assert "kind" in out.message


def test_skill_with_no_phases_round_trips_without_phases_key():
    """Codex review: a metadata-only `{"name": "x", "kind": "y"}` skill
    must NOT gain a synthesized `phases: []` on round-trip."""
    s_in = {"name": "metadata-only", "kind": "discipline"}
    out = parse_skill(s_in)
    assert out.ok
    assert out.value.to_dict() == s_in
    assert "phases" not in out.value.to_dict()


def test_skill_with_empty_phases_key_preserves_it():
    """When source declares `phases: []` explicitly, round-trip preserves
    the empty list (vs. dropping it like the metadata-only case)."""
    s_in = {"name": "x", "kind": "discipline", "phases": []}
    out = parse_skill(s_in)
    assert out.ok
    assert out.value.to_dict() == s_in


def test_invoke_phase_with_multiple_produces_returns_typed_code():
    """Codex review: walker stores at p["produces"][0] and validates
    every produced name — an invoke phase with >1 produces means the
    second+ can never be satisfied."""
    out = parse_phase({
        "name": "lint", "produces": ["a", "b"],
        "invoke": {"capability": "plugin", "verb": "lint_skill"},
    })
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD
    assert "exactly one" in out.message.lower() or "1" in out.message


def test_phase_with_empty_verbs_key_round_trips():
    """Codex review: live registry's scene-writer skill has `verbs: []`
    on its validate-constraints + generate phases. Round-trip must
    preserve the explicit empty list (vs. dropping it as a default)."""
    p_in = {"name": "validate-constraints", "produces": ["ok"], "verbs": []}
    out = parse_phase(p_in)
    assert out.ok
    p_out = out.value.to_dict()
    assert p_out == p_in
    assert "verbs" in p_out and p_out["verbs"] == []


def test_skill_non_contiguous_phase_indices_return_typed_code():
    """Codex review: walker advances by list position; phase indices
    must form 1..N when present (Spec 003)."""
    out = parse_skill({
        "name": "x", "kind": "discipline",
        "phases": [
            {"index": 1, "name": "a", "produces": ["x"]},
            {"index": 3, "name": "b", "produces": ["y"]},          # skip 2
        ],
    })
    assert not out.ok
    assert out.code == Codes.SKILL_PARSE_INVALID
    assert "contiguous" in out.message.lower() or "1..2" in out.message


def test_skill_mixed_indexed_un_indexed_phases_return_typed_code():
    out = parse_skill({
        "name": "x", "kind": "discipline",
        "phases": [
            {"index": 1, "name": "a", "produces": ["x"]},
            {"name": "b", "produces": ["y"]},                      # no index
        ],
    })
    assert not out.ok
    assert out.code == Codes.SKILL_PARSE_INVALID


# ── Codex round-7 review fixes ────────────────────────────────────────────
def test_null_invoke_returns_typed_code():
    """Codex review: `invoke: null` is not absent — a generated SkillDoc
    serializing an executable phase with null invoke must fail, not be
    silently walked as a step."""
    out = parse_phase({"name": "x", "produces": ["r"], "invoke": None})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD
    assert "null" in out.message.lower()


def test_null_phases_returns_typed_code():
    """Codex review: `phases: null` is not absent — must fail with
    SKILL_PARSE_INVALID instead of being silently normalized to []."""
    out = parse_skill({"name": "x", "kind": "discipline", "phases": None})
    assert not out.ok
    assert out.code == Codes.SKILL_PARSE_INVALID
    assert "null" in out.message.lower()


def test_empty_string_in_produces_returns_typed_code():
    """Codex review: `produces: [""]` must fail at the boundary; an
    empty output name reaches SkillRun.submit() and silently records
    a blank key."""
    out = parse_phase({"name": "x", "produces": [""]})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD


def test_empty_string_in_verbs_returns_typed_code():
    """Same empty-string discipline applies to `verbs` and `inputs`."""
    out = parse_phase({"name": "x", "produces": ["r"], "verbs": ["", "ok"]})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD


# ── Codex round-8 review fixes ────────────────────────────────────────────
def test_null_cue_returns_typed_code():
    """Codex review: `cue: null` is not absent — must fail at the
    boundary so the round-trip invariant doesn't synthesize an empty
    string the source didn't have."""
    out = parse_phase({"name": "x", "produces": ["r"], "cue": None})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD
    assert "cue" in out.message and "null" in out.message.lower()


def test_null_reference_returns_typed_code():
    out = parse_phase({"name": "x", "produces": ["r"], "reference": None})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD


def test_null_inputs_returns_typed_code():
    """Codex review: `inputs: null` would rewrite to `[]` on round-trip,
    breaking the invariant + letting malformed invoke contracts pass."""
    out = parse_phase({"name": "x", "produces": ["r"], "inputs": None})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD


def test_null_verbs_returns_typed_code():
    out = parse_phase({"name": "x", "produces": ["r"], "verbs": None})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD


def test_null_gate_verb_returns_typed_code():
    out = parse_phase({"name": "x", "produces": ["r"], "gate_verb": None})
    assert not out.ok
    assert out.code == Codes.PHASE_MISSING_FIELD


# ── Codes coverage ─────────────────────────────────────────────────────────
def test_skill_parse_codes_constants_land():
    """The Codes namespace gains the documented `SKILL_PARSE_*` + `PHASE_*`
    members the parse boundary returns (Spec 151 invariant b)."""
    assert Codes.SKILL_PARSE_INVALID == "skill_parse_invalid"
    assert Codes.PHASE_MISSING_FIELD == "phase_missing_field"
    assert Codes.PHASE_UNKNOWN_KIND == "phase_unknown_kind"


# ── ParseResult shape ──────────────────────────────────────────────────────
def test_parse_result_typed_envelope():
    out = parse_phase({"name": "x", "produces": ["r"]})
    assert isinstance(out, ParseResult)
    assert out.ok is True and out.code == "" and out.message == ""

    bad = parse_phase({})
    assert bad.ok is False and bad.code != ""
