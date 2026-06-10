---
spec_id: "268"
slug: test-fixture-derivation
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "169"
depends_on: ["169", "196", "147", "149"]
vision_goals: [4]
affects:
  - tests/conftest.py
  - tests/fixtures/
  - tests/test_fixture_derivation.py
---

# Spec 268 — test fixture derivation

## Why

Spec 169 ships CI coverage + flake gates. Test fixtures are
hand-authored (a fresh Engine + ad-hoc node inserts per test). As the
graph schema grows, fixtures rot (Spec 158 sweep). The derivation
discipline: a canonical fixture set is DERIVED from the live ontology
(every Schema gets a min-fixture + an edge-fixture), so a new node kind
auto-gets coverage; Spec 196 BDD scenarios populate from the same set.

## Done When

- [ ] **`tests/fixtures/derived.py`** generated from ontology Schemas.
- [ ] **Per-Schema min-fixture** = smallest valid instance.
- [ ] **Per-edge fixture** = source + target + edge.
- [ ] **Spec 196 BDD scenarios use derived fixtures** by default.
- [ ] **CI fails when a Schema lacks a derived fixture** (rule 8).
- [ ] Test: a new Schema auto-gets min-fixture; missing fixture trips CI.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 169 (CI gates) · Spec 196 (BDD) · Spec 149 (derive).
- Drift-derivation extended to test data.
