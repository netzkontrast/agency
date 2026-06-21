---
spec_id: "235"
slug: graph-neighbors-typed-paths
status: draft
state: draft
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
      max_hops=3) -> list[Path]`** where `Path = {nodes: list[Node],
      edges: list[Edge], length: int}` and `length == len(edges) ==
      len(nodes) - 1`. Bounded by `max_hops`; invariant: every returned
      `path.length <= max_hops`.
- [ ] **Built on `ctx.neighbors`** — one-hop composition, not new Cypher
      surface (the dormant-edge doctrine, CLAUDE.md). Invariant:
      `neighbors_path(n, [e], max_hops=1)` returns the SAME node-id set
      as `neighbors(n, e)` (composition agrees with the base case).
- [ ] **Type-safe** via Spec 056 `recall_typed` at each hop — invariant:
      every node in every returned path carries its registered Python
      type, never a bare property dict.
- [ ] **Edge-kind filter is enforced PER HOP** — invariant: for any
      returned path, `[e.kind for e in path.edges] == edges` (the
      requested edge sequence). A path that diverges from the typed
      template is never returned.
- [ ] **Cycle-safe** — invariant: no node-id repeats within a single
      path (the traversal carries a visited set); the function
      terminates in `O(branching_factor ** max_hops)`.
- [ ] **Failure modes** — `node_id` not found → empty list, never raise;
      unknown edge kind in `edges` → `Codes.UNKNOWN_EDGE_KIND` naming
      the offending edge; `max_hops > 10` → `Codes.PATH_LIMIT_EXCEEDED`
      (the doctrinal bound that keeps `analyze.graph` cheap).
- [ ] Test: 3-hop SERVES→PRODUCES path on a fixture returns the chain.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  an Intent I with two Invocations (V1, V2) that SERVES I, each
        with one Artefact (A1, A2) PRODUCES it
When:   ctx.neighbors_path(I.id, edges=["SERVES","PRODUCES"],
                            direction="in", max_hops=2)
Then:   result is a list of 2 Paths AND
        every path.length == 2 AND
        {p.nodes[-1].id for p in result} == {A1.id, A2.id} AND
        every path.edges has kinds ["SERVES","PRODUCES"] exactly

Given:  a node with a self-loop edge of the requested kind
When:   neighbors_path runs with max_hops=3
Then:   no returned path contains the node twice (cycle-safe invariant)
```

## Interconnects

- Spec 203 (graph query) consumes typed paths as building block.
- Spec 056 + Spec 171 (node-id guard coverage) extend per-hop.
- Spec 238 (story-time query) — first consumer for HAPPENS_AT chains.
- Spec 234 (export artefacts) — Novel→PRODUCES→ExportArtefact provenance.
- Spec 241 (character-knowledge) — Character→LEARNED_IN→Scene traversal.

## Open questions

1. **`max_hops` default.** **Recommend:** 3 — matches the 95th-percentile
   moat-query depth (SERVES→PRODUCES→DERIVES is the canonical 3-hop).
2. **Mixed direction.** Allow `direction=["in","out","out"]` per-hop?
   **Recommend:** yes — many traversals invert mid-chain
   (Intent→SERVES←Invocation→PRODUCES→Artefact).
3. **Path dedup.** Return all distinct paths or unique endpoint set?
   **Recommend:** all distinct paths; the caller dedupes by endpoint
   when needed — provenance often needs the path, not just the leaf.
