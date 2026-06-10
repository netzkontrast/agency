---
spec_id: "269"
slug: followup-status-derived-per-spec
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "149"
depends_on: ["149", "191", "259", "268"]
vision_goals: [4]
affects:
  - scripts/derive-docs
  - Plan/
  - tests/test_followup_derivation.py
---

# Spec 269 — per-spec Followup Implementation Status: derived

## Why

Spec 149 anchors derived docs (TODO + matrix + SkillDoc). Per CLAUDE.md
rule 4: "Per-spec deep state (test counts, file:line evidence, verbatim
Done / Still / Refinement) lives in each `Plan/NNN-…/spec.md`'s
`## Followup — Implementation Status (…)` section." These sections are
hand-authored, drift-prone. They should DERIVE from the same source as
the TODO row: tests counted from `affects:`, Done from frontmatter
`status: shipped` + commit log, Still from open issues / TODO items.

## Done When

- [ ] **`derive-docs` regenerates the Followup section** for shipped
      specs from the live source (test count, commit refs).
- [ ] **Hand-prose preserved** in a manually-edited zone; derived
      replaces a `<!-- derived -->` block.
- [ ] **CI fails when derived zones are stale.**
- [ ] **Spec 268 derived fixtures back the test counts.**
- [ ] Test: shipping a fixture spec auto-updates its Followup; manual
      prose unchanged.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 149 (parent); Spec 191 (matrix); Spec 268 (fixtures).
- Closes the CLAUDE.md rule-4 derivation gap.
