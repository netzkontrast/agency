---
spec_id: "235"
slug: graph-neighbors-typed-paths
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "125"
depends_on: ["125", "203", "056", "171"]
vision_goals: [4, 2]
affects:
  - agency/_context.py
  - tests/test_neighbors_typed_paths.py
---

# Spec 235 — graph-neighbors typed multi-hop paths

## Why

Spec 125 ships `ctx.neighbors` (one Cypher hop, property-dict lists).
Spec 203 (graph-query language) builds on it. Many moat queries need a
TYPED multi-hop path with edge-kind constraints — e.g. Intent →SERVES→
Invocation →PRODUCES→ Artefact in one composable call. Today that's
multiple `find`/`neighbors` round trips.

## Done When

- [ ] **`ctx.neighbors_path(node_id, edges=[...], direction="out",
      max_hops=3)`** — typed multi-hop traversal returning the path
      nodes + edges; bounded by `max_hops`.
- [ ] **Built on `ctx.neighbors`** — one-hop composition, not new Cypher
      surface (the dormant-edge doctrine, CLAUDE.md).
- [ ] **Type-safe** via Spec 056 `recall_typed` at each hop.
- [ ] Test: 3-hop SERVES→PRODUCES path on a fixture returns the chain.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 203 (graph query) consumes typed paths as building block.
- Spec 056 + Spec 171 (node-id guard coverage) extend per-hop.
