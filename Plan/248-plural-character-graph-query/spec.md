---
spec_id: "248"
slug: plural-character-graph-query
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "138"
depends_on: ["138", "203", "235", "216"]
vision_goals: [2, 4]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_plural_character_query.py
---

# Spec 248 — plural-character graph-query

## Why

Spec 138 ships CharacterSystem + Alter + PHOBIA_OF conflict matrix.
Common queries — "every scene where two max-pair alters co-fronted",
"all PHOBIA_OF cycles" — are exactly relational, perfect for Spec 203 +
Spec 235 typed paths. And the recognition discipline (never label
alters) composes with Spec 216 (shared name-exposure).

## Done When

- [ ] **PHOBIA_OF queries via `analyze.graph_query`** — find cycles,
      max-pair co-fronting, layer-crossing.
- [ ] **`switching_log` derived as typed path** (Spec 235).
- [ ] **Recognition check (138) uses Spec 216 shared substrate** when
      it ships.
- [ ] Test: a max-pair co-fronting query returns the offending scenes.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 203 (graph query) · Spec 235 (typed paths) · Spec 216 (name
  substrate).
