---
spec_id: "197"
slug: static-walkable-skills-resolve
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "078"
depends_on: ["078", "081", "152", "190"]
vision_goals: [4, 1]
affects:
  - Plan/078-static-walkable-skills/spec.md
  - tests/test_static_walkable_resolve.py
---

# Spec 197 — static-walkable-skills, resolve the clarification

## Why

Spec 078 (static-walkable-skills) is a research-first draft that "needs
clarification". The clarification is now answerable from the shipped
081 (walkable usage-skills derive) + 152 (typed Skill) + 190 (skill
reconciliation): the open question was whether a skill's phase graph
can be STATIC (authored once) vs DERIVED (from the docstring). The
answer is the 081 model — derived by default, authored override —
so 078 resolves to "fold into 081's derive model, document the override
path, cancel the standalone static-skill concept."

## Done When

- [ ] **Spec 078 gets an explicit verdict** — folded into the 081
      derive model with a documented authored-override path (not a new
      static-skill mechanism).
- [ ] **The override path is tested** — an authored phase graph
      overrides the derived one for one capability.
- [ ] **078 TODO row flips to Closed/Superseded → 081** with a pointer.
- [ ] Test: authored override wins over derived; default derive
      unchanged.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 081 (walkable usage-skills) is the resolution surface.
- Spec 152 (typed Skill) + Spec 190 (reconciliation) are the model.

## Open questions

1. Any genuine static-only need? **Recommend**: no — the derive+override
   model covers it; cancel the standalone concept.
