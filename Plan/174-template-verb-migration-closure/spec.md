---
spec_id: "174"
slug: template-verb-migration-closure
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "060"
depends_on: ["060", "153", "032", "149"]
vision_goals: [4, 7]
affects:
  - agency/capabilities/jules/_main.py
  - agency/capabilities/document/_main.py
  - agency/capabilities/analyze/_main.py
  - tests/test_template_verb_migration.py
---

# Spec 174 — template verb-migration closure (Phase 5)

## Why

Spec 060 (templates-schemas-agent-instructions) is "Mostly shipped" —
Phases 1+2+3+4+6 complete, but "Phase 5 (verb migration to
`ctx.template()`) remains as opt-in: dogfood.render migrated;
jules._main.preambles + document.explain + analyze.run/improve can flip
when iteration pressure justifies." The enhancement-wave pressure now
justifies it: a migrated verb renders from a vendored Template (Goal 7,
files-render-from-graph) instead of an inline literal, and Spec 153
closed schema coverage so the validate side is ready.

## Done When

- [ ] **jules preambles + document.explain + analyze.run/improve flip
      to `ctx.template()`** (close Phase 5).
- [ ] **Each migrated verb's output VALIDATES_AGAINST a Schema**
      (Spec 153 coverage) — the generate/validate pair is whole.
- [ ] **No inline template literal remains** in the migrated verbs
      (derivability audit, Spec 149).
- [ ] Test: each migrated verb renders from its Template; a missing
      Template field fails validation.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 153 (schema coverage) is the validate-side prerequisite.
- Spec 060 is the parent substrate.
- **Drift-derivation chain** (149).

## Open questions

1. Migrate all four now or stage? **Recommend**: stage by capability
   (one PR each) to keep blast radius small — Spec 060's own pattern.
