---
spec_id: "272"
slug: jules-skills-derive
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "013"
depends_on: ["013", "081", "163", "149"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/jules/_main.py
  - tests/test_jules_skills_derive.py
---

# Spec 272 — Jules skills: derive from capability docstring

## Why

Spec 013 ships 6 Jules skills + AGENCY_PROTOCOL + lint + flag matrix.
Like the broader SkillDoc derive (Spec 080/081), these should derive
from their host code (the Jules cap docstring) instead of duplicating —
matching the SkillDoc discipline already shipped for every other cap
(Spec 163 closure).

## Done When

- [ ] **The 6 Jules skills derive** from `agency/capabilities/jules/_main.py`
      docstring via Spec 081 walker; literal SKILL.md files retired.
- [ ] **AGENCY_PROTOCOL §10 references regenerate** on docstring change
      (Spec 149 drift gate).
- [ ] **flag matrix derived** from the live flag set, not hand-pinned.
- [ ] Test: docstring change updates skill bodies + matrix in one
      derive pass; CI fails on a hand-edit collision.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 081 (walkable usage-skill derive) is the pattern.
- Spec 163 (progressive-disclosure closure) is the parallel discipline.
- **Drift-derivation chain** (149).
