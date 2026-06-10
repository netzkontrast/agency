---
spec_id: "196"
slug: bdd-gherkin-driver-impl
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "077"
depends_on: ["077", "147", "169", "152"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/develop/_bdd.py  (NEW)
  - tests/test_bdd_gherkin.py
---

# Spec 196 — BDD/Gherkin test-authoring driver

## Why

Spec 077 (bdd-gherkin-tests) is a research-first backlog draft. The
research question — "how does the engine author behaviour tests from a
spec's Done-When list?" — is now answerable: each Done-When bullet is a
behaviour, and the Spec 147 Driver can render it as a Gherkin scenario +
a pytest skeleton (`output_config.format`). This closes the loop between
a spec's acceptance criteria and its test suite, which the CI
coverage gate (Spec 169) then enforces.

## Done When

- [ ] **`develop.author_bdd(spec_id)`** reads a spec's Done-When list
      and emits Gherkin scenarios + pytest skeletons (one per bullet),
      via the Spec 147 Driver; degrades to a structured stub without
      `[anthropic]`.
- [ ] **Generated tests link to the spec** (provenance: PRODUCES from
      the spec's Intent).
- [ ] **The CI coverage gate (Spec 169) counts BDD scenarios** toward
      the per-capability floor.
- [ ] Test: a fixture spec yields one scenario per Done-When bullet
      (mocked Driver).
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · Spec 169 (coverage gate) consumes output.
- Spec 152 (typed Skill) — the authoring step is a walkable phase.

## Open questions

1. Author at spec-draft time or implement time? **Recommend**:
   implement time (the Done-When is stable by then); draft-time is noisy.
