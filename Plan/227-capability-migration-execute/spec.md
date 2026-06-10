---
spec_id: "227"
slug: capability-migration-execute
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "111"
depends_on: ["111", "147", "182", "183"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/
  - tests/test_capability_migration.py
---

# Spec 227 — capability-migration plan execution

## Why

Spec 111 (capability-migration) is the PLAN — 17 existing caps + 2
in-flight domain caps mapped to the adoption surface + migration shape +
PR sequencing. A plan that isn't executed rots. The enhancement waves
(146-226) ARE much of the adoption the plan scoped (LLM-driver,
output-budget, derived docs); this spec reconciles the 111 plan against
what the waves shipped, executes the remaining migrations, and the
opportunity detector (Spec 183) surfaces caps that should adopt a verb
they're re-implementing.

## Done When

- [ ] **The 111 migration plan is reconciled against the shipped waves**
      (derived — which migrations the 146-226 waves already did).
- [ ] **The remaining migrations execute** — each cap adopts the
      substrate it was re-implementing (the opportunity detector, Spec
      183, ranks them).
- [ ] **Cluster coherence (Spec 182) re-checked** post-migration.
- [ ] **111 row flips toward Shipped** with a derived completion %.
- [ ] Test: a cap re-implementing a substrate helper is flagged + migrated.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 183 (opportunity detector) ranks the migrations.
- Spec 182 (cluster coherence) validates the result.

## Open questions

1. Big-bang or incremental? **Recommend**: incremental, one cap per PR
   (the 111 sequencing) — the waves already proved the pattern.
