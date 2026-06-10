---
spec_id: "153"
slug: template-schema-coverage-closure
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "004"
depends_on: ["004", "060", "032", "149"]
vision_goals: [4, 7]
affects:
  - agency/_templates.py
  - agency/_lints/_schema_coverage.py
  - tests/test_template_schema_coverage.py
---

# Spec 153 — Template/schema coverage closure

## Why

Spec 004 (wire the generate/validate loop for uncovered node kinds) is
Not Started. Spec 060 shipped the substrate (loader + dataclasses +
materialiser) + 15 schema files + 7 template files, but Phase 5 (verb
migration to `ctx.template()`) is opt-in and most node kinds still have
NO schema — so the generate/validate pair (CORE.md §"Schemas &
templates") is half-wired. This closes the coverage gap with a derived
audit, not a hand-maintained list.

## Done When

- [ ] **`_check_schema_coverage` audit** lists every node label the
      live ontology declares vs every label with a Schema; the delta is
      the uncovered set (derived — Spec 149, rule 8).
- [ ] **`agency_doctor` reports `schema_coverage`** as a fraction.
- [ ] **Schemas authored for the highest-traffic uncovered kinds**
      (the audit ranks by graph node-count — derive the priority).
- [ ] **`generate → validate` round-trip test** per newly-covered kind:
      a Template renders an Artefact a Schema validates; a missing field
      fails (the CORE.md proven-runnable pattern, extended).
- [ ] TODO row + drift clean.

## Interconnects

- **Drift-derivation chain** (149): `schema_coverage` is derived.
- Spec 060 (templates-schemas) is the substrate this exercises.
- Spec 152 (typed Skill/Phase) is the parse-side sibling of this
  generate/validate discipline.

## Open questions

1. Author all uncovered schemas, or only graph-present kinds?
   **Recommend**: only kinds with ≥1 live node first (the rest are
   speculative); the audit ranks by count.
