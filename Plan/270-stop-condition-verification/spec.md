---
spec_id: "270"
slug: stop-condition-verification
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "_planning/charter"
depends_on: ["261", "264", "150", "191"]
vision_goals: [6]
affects:
  - Plan/_planning/charter.md
  - scripts/check-charter-stop-condition
  - tests/test_stop_condition.py
---

# Spec 270 — charter stop-condition verification

## Why

The charter's stop condition is "no existing spec has a remaining
enhancement on any of the five gap axes". Spec 261 audits closure;
Spec 264 self-improves. The STOP CONDITION itself needs verification:
a measurable predicate that returns `closure: bool` + `remaining: [...]`.
When closure flips true, the wave program is complete; when it would
flip back (a new gap appears), Spec 264 self-improves to close it.

## Done When

- [ ] **`scripts/check-charter-stop-condition`** computes the predicate
      against the live tree.
- [ ] **Public closure status** rendered in the alignment matrix (Spec
      191) — "5/5 gap axes covered for X of Y existing specs".
- [ ] **Self-test** — flip a gap-axis coverage off in a fixture, assert
      stop returns false with the right gap named.
- [ ] **CI surfaces closure trend** over time.
- [ ] Test: predicate correct on current state + on synthetic
      regressions.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 261 (closing audit); Spec 264 (self-improvement); Spec 191
  (matrix); Spec 150 (dogfood).
- The charter's terminal proof.
