---
spec_id: "163"
slug: progressive-disclosure-closure
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "031"
depends_on: ["031", "080", "081", "149"]
vision_goals: [1, 4]
affects:
  - agency/_skilldoc.py
  - tests/test_progressive_disclosure_closure.py
---

# Spec 163 — Progressive-disclosure closure

## Why

Spec 031 (skills-progressive-disclosure) is Partial — "per-spec skill
rendering: emit_skill, references, bash wrappers; active work on main".
Specs 080/081 generalized SkillDoc derivation, which means the per-spec
emit_skill path now has a single canonical source. This spec finishes
031 by routing emit_skill through the 080/081 derive engine (no
literal duplication) and deriving the references/ + bash-wrapper set
instead of hand-maintaining them.

## Done When

- [ ] **`emit_skill` derives from the module docstring** (080/081), not
      a per-spec literal — close the 031 active-work item.
- [ ] **references/ + bash wrappers generated** from the live verb set
      (derive, Spec 149), so a new verb auto-appears.
- [ ] **No SkillDoc body duplicates a docstring** (the derivability
      audit, CLAUDE.md) — asserted by a lint.
- [ ] Test: change a docstring `Use when:` line → emit_skill output
      updates; references regenerate on a new verb.
- [ ] TODO row + drift clean.

## Interconnects

- **Drift-derivation chain** (149).
- Spec 080/081 (SkillDoc derive) is the engine.

## Open questions

1. Keep bash wrappers, or fold into Spec 079 CLI mirror? **Recommend**:
   fold — the 079 mirror already exposes every verb; per-spec wrappers
   are redundant. Deprecate them here.
