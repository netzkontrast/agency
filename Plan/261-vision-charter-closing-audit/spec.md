---
spec_id: "261"
slug: vision-charter-closing-audit
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "_planning/charter"
depends_on: ["191", "149", "150", "258"]
vision_goals: [6]
affects:
  - Plan/_planning/charter.md
  - scripts/check-charter-closure
  - tests/test_charter_closure.py
---

# Spec 261 — vision charter: closing audit

## Why

The enhancement charter (Plan/_planning/charter.md) defines a stop
condition: "no existing spec has a remaining enhancement on any of the
five gap axes". This spec ships the STANDING audit that measures
closure — for each existing spec, derive which gap axes have an
enhancement shipped; flag any uncovered axis. The dogfood loop (Spec
150) then proposes enhancements for uncovered axes; the live alignment
matrix (Spec 191) tracks progress.

## Done When

- [ ] **`scripts/check-charter-closure`** derives the gap-axis × spec
      matrix; flags uncovered cells.
- [ ] **A new spec without a Goal-mapping check is rejected** (Spec 149
      drift extension).
- [ ] **The charter's "stop condition" is computed**, not asserted.
- [ ] **CI surfaces the closure status** as a percentage.
- [ ] Test: closure matrix correctly identifies uncovered axes on a
      fixture.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 191 (matrix) · Spec 149 (drift) · Spec 150 + 258 (dogfood loop).
- The charter's measurable closing condition.
