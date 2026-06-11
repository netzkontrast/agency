---
spec_id: "152"
slug: typed-skill-phase-parse-boundary
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "003"
depends_on: ["003", "081", "026", "149"]
vision_goals: [4, 3]
affects:
  - agency/skill.py
  - agency/_skill_parse.py  (NEW)
  - tests/test_skill_phase_parse.py
---

# Spec 152 — Typed Skill/Phase parse/validate boundary

## Why

Spec 003 (typed `Skill`/`Phase` parse/validate boundary) is Not
Started, yet the walkable-skill surface has exploded — Specs 080/081
derive SkillDocs, Specs 130/142/145 ship multi-phase walks, Spec 026
promotes Skills to graph nodes. Every one of those parses phase dicts
ad hoc. A single typed boundary (`parse_skill(dict) -> Skill`,
`validate_phase(phase) -> Result`) removes the scattered parsing and
gives the walker (Spec 018) one validation point.

## Done When

- [ ] **`Skill` / `Phase` dataclasses** with a `parse_skill(dict) ->
      Result[Skill, Codes.SKILL_PARSE_*]` / `validate_phase(Phase) ->
      Result[Phase, Codes.PHASE_*]` boundary at `agency/_skill_parse.py`.
      Typed variants: `HardGatePhase`, `ElicitPhase`, `StepPhase` (CORE.md
      §"Skills are atomic, gated").
- [ ] **`develop.skill_walk` routes through it** — phase dicts validate
      ONCE at parse, not per-step; bad phases fail fast with a typed
      error (Spec 151 Codes).
- [ ] **Hard-gate + elicit phases are typed variants** (CORE.md §"Skills
      are atomic, gated").
- [ ] **Measurable invariants** (rule 8):
      (a) `parse_clean(live_registry.skills) == live_registry.skills`
      (every registered skill round-trips); (b) ad-hoc-parse callsites
      (`grep_ast` for `phase\[`/`phase.get(` outside the boundary module)
      decreases monotonically — invariant zero after one cycle;
      (c) every `Phase` variant maps to ≥ 1 typed `Codes.PHASE_*` failure
      member.
- [ ] Every walkable skill in the live registry parses clean (migration
      audit, not a snapshot count — rule 8).
- [ ] Test: a malformed phase fails `validate_phase`; every registered
      skill round-trips through `parse_skill`.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a SkillDoc declares phases=[{"kind": "hard-gate", "predicate":
        "tests_green"}, {"kind": "step", "text": "..."}]
When:   develop.skill_walk(name=...) calls parse_skill on the dict
Then:   Skill(phases=[HardGatePhase(predicate="tests_green"),
        StepPhase(text="...")]) returned; walker dispatches by type
        with no per-step dict introspection

Given:  a phase dict with kind="hard-gate" but no predicate key
When:   validate_phase runs
Then:   Result.failure(Codes.PHASE_MISSING_PREDICATE,
        loc="<skill>.phases[0]") — walker aborts before phase 0 runs
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Silent skip on unknown kind | new phase kind added without variant | invariant (c) — Codes coverage | reject at parse with `Codes.PHASE_UNKNOWN_KIND` |
| Ad-hoc parser reintroduction | a verb reads `phase["kind"]` directly | invariant (b) — grep_ast monotone | lint per Spec 151 family |
| SkillDoc drift across reload | derive (Spec 081) consumes stale dict | parse_clean round-trip test | single parse point upstream of derive |
| LLM driver generates malformed phase | Spec 147 Driver synthesizes a SkillDoc with bad shape | typed `Codes.PHASE_*` at parse boundary | reject before walker dispatch; never trust freeform LLM SkillDoc output |

## Interconnects

- **Drift-derivation chain** (149): SkillDoc derive (081) consumes the
  typed `Skill` instead of re-parsing.
- Spec 026 (`skills` cap) promotes the typed `Skill` to a graph node.
- Spec 018 (walker) is the primary consumer.
- Spec 151 (Codes coverage) supplies the `Codes.PHASE_*` /
  `Codes.SKILL_PARSE_*` members this boundary returns.
- Spec 153 (template/schema coverage) is the sibling generate-side
  discipline — parse here, generate there, single Codes namespace.
- Spec 156 (wet pressure) re-uses `parse_skill` to load adversarial
  scenarios without re-implementing the parse.
- Spec 160 (CLI `--chain`) — `ChainStep` reuses the same typed
  parse boundary so YAML chain steps validate once at parse, not at
  step N.
- Spec 158 (capability scaffold) — typed `Skill`/`Phase` is one of
  the contracts the scaffold marker implies the capability satisfies.

## Open questions

1. Pydantic or stdlib dataclass? **Recommend**: stdlib dataclass +
   a tiny validate fn — matches the engine's no-heavy-dep posture; the
   ontology already enforces graph-side.
2. Variant union via `match` or `isinstance`? **Recommend**: `match`
   on `Phase` subclasses — Python 3.10+ is the floor; pattern-matching
   forces exhaustiveness (a NEW variant trips every walker).
