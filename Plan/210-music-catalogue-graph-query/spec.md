---
spec_id: "210"
slug: music-catalogue-graph-query
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "097"
depends_on: ["097", "203", "146", "154"]
vision_goals: [2, 1]
affects:
  - agency/capabilities/music/_main.py
  - tests/test_music_catalogue_query.py
---

# Spec 210 — music catalogue graph-query + budget

## Why

Spec 097 (music-catalogue) ships 13 verbs + `db_init` tracking the
release catalogue. Catalogue queries ("every track on albums released
in Q1 that passed the audio gate") are exactly the relational moat
query Spec 203 generalizes — and catalogue listings are high-token
output (the charter's gap #1). This wires the catalogue onto the
graph-query surface + the output budget.

## Done When

- [ ] **Catalogue queries route through `analyze.graph_query`** (Spec
      203) — relational catalogue questions answered in one call.
- [ ] **List verbs honor the output budget** (Spec 146/154).
- [ ] **The deferred `clusters/catalogue.py` split lands** (094-family
      migration).
- [ ] Test: a relational catalogue query returns the expected subgraph;
      a large listing captures-and-recalls.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 203 (graph query) · **output-budget** (146/154).
- The catalogue is part of the music provenance moat (Goal 2).

## Open questions

1. Keep `db_init` SQLite or fold into the graph? **Recommend**: the
   graph IS the store (Goal 7) — `db_init` becomes a rendered view;
   defer the migration to a Slice-2 if it risks the shipped surface.
