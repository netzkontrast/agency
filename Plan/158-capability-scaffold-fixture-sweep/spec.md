---
spec_id: "158"
slug: capability-scaffold-fixture-sweep
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "024"
depends_on: ["024", "016", "054", "149"]
vision_goals: [4]
affects:
  - agency/capabilities/*/  (scaffold markers)
  - scripts/check-drift
  - tests/test_scaffold_sweep.py
---

# Spec 158 — Capability scaffold + fixture sweep

## Why

Spec 024 (capability-authoring-discipline) is Partial — block-mode lint
fires only when `# agency-scaffold: v1` is present, and its Followup
names the remaining task: "Sweep of existing capabilities for marker
addition". Spec 016's Phase 5 fixture cleanup is also Partial. Both are
mechanical sweeps that should be DONE and then GUARDED so new
capabilities can't ship without the marker (the drop-in-capability bar,
CLAUDE.md).

## Done When

- [ ] **Every capability carries `# agency-scaffold: v1`** (sweep),
      so block-mode lint (Spec 024) applies uniformly.
- [ ] **`scripts/check-drift` gains a marker-presence check** (Spec 054
      family) — a new `capabilities/<name>/` with no scaffold marker
      fails CI.
- [ ] **Spec 016 Phase-5 fixture cleanup completed** — orphan fixtures
      removed (derived inventory, not a hand list).
- [ ] Test: a capability fixture missing the marker trips check-drift;
      the live sweep reports 0 unmarked.
- [ ] TODO row + drift clean.

## Interconnects

- **Drift-derivation chain** (149): the unmarked-capability inventory is
  derived.
- Spec 016 (authoring doctrine) is the parent discipline.
- Spec 054 (drift management) hosts the new check.

## Open questions

1. Backfill `v1` or introduce `v2` with stricter rules? **Recommend**:
   backfill `v1` (matches existing lint), reserve `v2` for a future
   tightening.
