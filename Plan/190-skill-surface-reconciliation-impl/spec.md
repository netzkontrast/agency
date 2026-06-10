---
spec_id: "190"
slug: skill-surface-reconciliation-impl
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "071"
depends_on: ["071", "152", "163", "149"]
vision_goals: [1, 4]
affects:
  - agency/capabilities/
  - skills/
  - tests/test_skill_surface_reconciliation.py
---

# Spec 190 — skill-surface reconciliation implementation

## Why

Spec 071 (skill-surface-reconciliation) is WARN-accepted — CORE.md
flags that a skill name lives on TWO surfaces (`ontology.skills` key +
`skills/<name>/SKILL.md`) and they can diverge (`tdd` ↔
`test-driven-development`), with "one name per skill across both
surfaces" as the canonical direction. The typed Skill boundary (Spec
152) + derived SkillDocs (Spec 163) make reconciliation mechanical:
derive both surfaces from one source so they CAN'T diverge.

## Done When

- [ ] **One canonical skill name per skill** — the `ontology.skills`
      key and the `skills/<name>/` folder derive from a single source
      (Spec 152 typed `Skill`).
- [ ] **The divergent pairs reconciled** (e.g. `tdd` →
      `test-driven-development` alias-and-deprecate).
- [ ] **A lint fails when the two surfaces diverge** (Spec 149 drift).
- [ ] **`develop.skill_walk` resolves either name** during the
      deprecation window (no break).
- [ ] Test: a divergent fixture trips the lint; both names resolve to
      one walk.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 152 (typed Skill) is the single source.
- Spec 163 (progressive disclosure) derives the SKILL.md surface.
- **Drift-derivation chain** (149).

## Open questions

1. Which name wins on a divergence? **Recommend**: the kebab
   marketplace name (`test-driven-development`) — matches the
   superpowers convention + the using-agency meta-skill.
