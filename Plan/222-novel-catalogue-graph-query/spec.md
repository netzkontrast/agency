---
spec_id: "222"
slug: novel-catalogue-graph-query
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "106"
depends_on: ["106", "203", "146", "154"]
vision_goals: [2, 1]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_catalogue_query.py
---

# Spec 222 — novel catalogue graph-query + budget

## Why

Spec 106 (novel-catalogue) tracks a novelist's works. Cross-work queries
("every scene across my novels that uses the betrayal motif", "all
chapters flagged by a sensitivity reader") are the relational moat query
Spec 203 generalizes, and catalogue listings are high-token output (the
charter's gap #1). This wires the novel catalogue onto the graph-query
surface + the output budget.

## Done When

- [ ] **Catalogue queries route through `analyze.graph_query`** (Spec
      203) — cross-work relational questions in one call.
- [ ] **List verbs honor the output budget** (Spec 146/154).
- [ ] Test: a cross-work motif query returns the expected subgraph; a
      large listing captures-and-recalls.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 203 (graph query) · **output-budget** (146/154).
- Part of the novel provenance moat (Goal 2).

## Open questions

1. Per-author or global catalogue? **Recommend**: per-author scope by
   default (the owner edge); a shared-world catalogue is a Slice-2.
