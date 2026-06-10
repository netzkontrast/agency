---
spec_id: "259"
slug: derived-doc-self-test
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "149"
depends_on: ["149", "191", "175", "177"]
vision_goals: [4]
affects:
  - scripts/check-doc-drift
  - tests/test_derived_doc_self_test.py
---

# Spec 259 — derived-doc discipline: self-test

## Why

Spec 149 anchors the drift-derivation chain. The discipline derives
TODO/matrix/SkillDoc — but does it derive ITSELF? A self-test:
mutate the registry, run derive-docs, assert every derived surface
(TODO row, alignment matrix Goal status, install marketplace
description, Skill triggers, slash-command family) updates correctly
in one pass. The standing proof that drift is dead.

## Done When

- [ ] **End-to-end derive-docs self-test** — mutate a fixture
      capability, assert all derived surfaces update.
- [ ] **`check-doc-drift` includes itself** in the audit (meta-coverage).
- [ ] **Failure modes are surfaceable** — a partial derivation reports
      which surface fell behind.
- [ ] Test: full self-test green on the live tree; a deliberate gap
      trips.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 149 (parent); Spec 191 (matrix); Spec 175 (install); Spec 177
  (reference audit).
- **Drift-derivation chain** completion.
