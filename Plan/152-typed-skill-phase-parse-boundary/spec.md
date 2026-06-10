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

- [ ] **`Skill` / `Phase` dataclasses** with a `parse_skill` /
      `validate_phase` boundary at `agency/_skill_parse.py`.
- [ ] **`develop.skill_walk` routes through it** — phase dicts validate
      ONCE at parse, not per-step; bad phases fail fast with a typed
      error (Spec 151 Codes).
- [ ] **Hard-gate + elicit phases are typed variants** (CORE.md §"Skills
      are atomic, gated").
- [ ] Every walkable skill in the live registry parses clean (migration
      audit, not a snapshot count — rule 8).
- [ ] Test: a malformed phase fails `validate_phase`; every registered
      skill round-trips through `parse_skill`.
- [ ] TODO row + drift clean.

## Interconnects

- **Drift-derivation chain** (149): SkillDoc derive (081) consumes the
  typed `Skill` instead of re-parsing.
- Spec 026 (`skills` cap) promotes the typed `Skill` to a graph node.
- Spec 018 (walker) is the primary consumer.

## Open questions

1. Pydantic or stdlib dataclass? **Recommend**: stdlib dataclass +
   a tiny validate fn — matches the engine's no-heavy-dep posture; the
   ontology already enforces graph-side.
