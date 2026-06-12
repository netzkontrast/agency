---
spec_id: "077"
slug: bdd-gherkin-tests
status: draft
last_updated: 2026-06-06
owner: "@agency"
depends_on: ["011", "053"]   # spec acceptance already uses Gherkin; the test-marker discipline
research_first: true
affects:
  - tests/                              # a Gherkin/BDD pilot (feature files + step defs)
  - docs/vision/                        # the testing-style decision
estimated_jules_sessions: 0
domain: meta
wave: 5
---

# Spec 077 — BDD / Gherkin test migration (research-first)

## Why

User directive (2026-06-06): *"add a Gherkin spec — to rewrite the current tests
or improve them with Gherkin — the spec should include research first."* The suite
is plain pytest; behaviour intent lives in docstrings. Several specs ALREADY carry
Gherkin acceptance scenarios (Spec 011 anchors 119.1/133.x; the `spec_validate`
lint checks for Scenario/Given/When/Then). Connecting those executable-spec
anchors to the actual tests would make behaviour the first-class artefact.

## Research first (mandatory — the spec ships the research before any migration)

- **Frameworks:** `pytest-bdd` vs `behave` vs `radish` vs staying pytest with a
  Gherkin-style naming convention. Token cost, maintenance, IDE support, how each
  composes with the existing `Engine(":memory:")` fixtures + Spec 053 markers.
- **Scope:** which tests benefit (behaviour/acceptance — e.g. `shell`, `gate`,
  `delegate`) vs which don't (pure unit/snapshot — e.g. `_apply_filter` param
  tables, the invariant guards).
- **The bridge:** can the Gherkin in `Plan/NNN/spec.md` acceptance sections become
  the actual `.feature` files (one source of truth, spec ↔ test)?
- Record the research as a graph reflection + a short report.

## Done When

- [ ] **Research report** with a recommendation (adopt `pytest-bdd` / partial /
  reject), grounded in the survey above.
- [ ] **A pilot:** migrate ONE capability's behaviour tests to `.feature` +
  step-defs as a proof (recommend `shell` — clear Given/When/Then: given an
  allowlisted command, when run with a filter, then only the slice + a recorded
  run). Both styles green side-by-side.
- [ ] **A decision** (adopt cluster-wide / pilot-only / reject) with the trade-off
  in the spec body + spec-panel review — no wholesale rewrite without the verdict.

## Migration

Additive pilot: the new `.feature` tests run alongside the existing pytest; no
existing test is deleted until the decision lands. If adopted, migration is
incremental, capability by capability.

## Open Questions

1. **One source of truth.** Ideal: the spec's Gherkin acceptance IS the feature
   file. Needs a convention (where the `.feature` lives vs `Plan/NNN/spec.md`).
2. **Run cost.** `pytest-bdd` adds collection overhead; measure against Spec 053's
   fast-slice discipline.

## Evidence

- Spec 011 (Gherkin acceptance anchors already in spec bodies) + `_predicates.
  spec_validate` (the Gherkin lint).
- Spec 053 (test markers + fast slices the BDD layer must respect).
- User directive (2026-06-06): a research-first Gherkin spec.

## Followup — Implementation Status (2026-06-12)

**Verdict:** Drafted (backlog / WARN-accepted / cluster-master). Tracked
in TODO.md's Verdicts row; no Slice 1 commitment beyond the spec body.
For the autonomous-completion goal stop condition (2), this spec is
classified as drafted-by-doctrine, not pending-implementation.

