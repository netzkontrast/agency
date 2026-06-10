---
spec_id: "172"
slug: analyzer-linter-expansion
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "057"
depends_on: ["057", "166", "167", "149"]
vision_goals: [4]
affects:
  - agency/capabilities/analyze/_main.py
  - tests/test_axis_registry_expansion.py
---

# Spec 172 — analyzer rule-axis registry expansion proof

## Why

Spec 057 made the analyzer axis registry drop-in (each `_<tool>.py`
declares `AXIS_PREFIXES`; the registry unions with longest-prefix-first
+ cross-axis collision detection). Specs 166 + 167 add mypy/pylint/
semgrep/networkx. This spec is the REGISTRY-level proof that the
expansion didn't break the union invariant — a standing test that the
registry rebuilds clean for ANY combination of installed analyzers, so
future linters drop in without a registry edit.

## Done When

- [ ] **Registry-rebuild property test** — for every subset of the
      installed analyzers, the union builds without a collision and
      longest-prefix-first resolution holds.
- [ ] **A deliberately-colliding fixture analyzer** is rejected with a
      typed error (Spec 151 Codes), proving the guard.
- [ ] **`agency_doctor` lists the live axis map** (derived).
- [ ] Test: the property test over the analyzer power-set; collision
      fixture rejected.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 166 + 167 (new analyzers) are the expansion this guards.
- **Drift-derivation chain** (149): axis map derived.

## Open questions

1. Power-set test too slow at N analyzers? **Recommend**: cap at
   pairwise + all-on (the collisions that matter are pairwise).
