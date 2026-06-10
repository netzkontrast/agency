---
spec_id: "226"
slug: thinking-cap-slice2-wet
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "110"
depends_on: ["110", "204", "147", "150"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/thinking/_main.py
  - tests/test_thinking_cap_slice2.py
---

# Spec 226 — thinking capability Slice 2 (remaining methods + wet)

## Why

Spec 110 (thinking-capability) is Partial — Slice 1 shipped 11 verbs;
Slice 2 names "4 remaining methods (pre_commitment, bayesian_update,
if_then_else, analogy_map) + 2 composites + 2 walkable skills + intent
capability migration". The wet-method pattern (Spec 204, applied to the
intent cap) generalizes here: the 4 remaining methods ship with the
optional `run=True` wet path from the start, and the intent-cap
migration (110's deferred task) reuses 204's wiring.

## Done When

- [ ] **The 4 remaining methods ship** (pre_commitment / bayesian_update
      / if_then_else / analogy_map) with the Spec 204 wet `run=True`
      pattern built in.
- [ ] **The 2 composites + 2 walkable skills ship** (red-team-pass,
      decision-discipline).
- [ ] **Intent-capability migration** (110's deferred task, per Spec
      111) — the 8 intent methods become thin wrappers over the thinking
      cap.
- [ ] **Wet outputs become Reflections** (Spec 150 dogfood loop).
- [ ] **110 row flips toward Shipped.**
- [ ] Test: each new method returns a scaffold (run=False) + a filled
      analysis (run=True, mocked); intent wrappers delegate.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 204 (intent wet methods) is the pattern · **dogfood** (150).
- Spec 111 (migration plan) governs the intent-cap wrapper move.

## Open questions

1. Migrate intent cap or deprecate it? **Recommend**: thin-wrapper
   migration (Spec 091's methods stay callable, delegate to thinking).
