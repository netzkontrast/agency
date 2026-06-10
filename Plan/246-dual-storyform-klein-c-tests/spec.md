---
spec_id: "246"
slug: dual-storyform-klein-c-tests
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "136"
depends_on: ["136", "120", "147", "219"]
vision_goals: [4]
affects:
  - tests/test_klein_c_property.py
---

# Spec 246 — dual-storyform Klein-c property tests

## Why

Spec 136 ships StoryformSet + Klein-c inversion check + Vortex
transitions. The Klein-c check is decidable but currently tested on a
single canonical KP fixture. As more dual-storyform novels are
authored, the inversion check needs property-level tests: every legal
StoryformSet satisfies Klein-c by construction; an illegal pair fails
with a precise diagnostic. The V₄ structure (two Z₂ flips) is testable
as an algebraic property, not just a fixture.

## Done When

- [ ] **Property test over the Klein-c V₄ structure** — generate legal
      pairs; assert check passes. Inject a single-slot mutation; assert
      check fails with the precise slot named.
- [ ] **Spec 219 storyform-suggestion uses these tests as the gate**
      when proposing inversion partners.
- [ ] **Diagnostic improvement** — failed checks return which Z₂ flip
      broke, not just "non-inverted".
- [ ] Test: property test green; mutated fixture fails with named slot.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 120 (coherence check) is the algebraic sibling.
- Spec 219 (suggest_storyform) uses these as gates.
