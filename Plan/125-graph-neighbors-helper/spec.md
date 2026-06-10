---
spec_id: "125"
slug: graph-neighbors-helper
status: draft
last_updated: 2026-06-09
owner: "@agency"
depends_on: ["002", "084"]
affects:
  - agency/capability.py
  - agency/capabilities/novel/_main.py
  - agency/capabilities/music/_main.py
  - tests/test_capability_context.py
domain: substrate / graph
mvp-source:
  - "Round-1 sc-analyze F4 advisory (2026-06-09): CHAPTER_OF declared but never traversed"
---

# Spec 125 — `ctx.neighbors(node_id, edge)` Substrate Helper

## Why

A Round-1 sc-analyze advisory (deliberately deferred, now due): both
domain caps declare edges they never traverse. `chapter_report`,
`render_manuscript`, `list_chapters`, `novel_progress` all do
`ctx.find("Chapter")` — a full-label scan — then filter by
`c.get("novel") == novel_id` in Python, even though `CHAPTER_OF`
edges exist. Music's AlbumClaim scans have the same shape at 4 sites.
The edges are write-only decoration; the O(N) scan grows with every
novel in the graph; and the substrate offers no sanctioned traversal
shorthand, which is WHY the caps fell back to scans.

## Done When

- [ ] **`ctx.neighbors(node_id, edge, direction="in") -> list[dict]`**
      on `CapabilityContext` — one Cypher hop:
      `MATCH (n)-[:EDGE]->(t) WHERE t.id = $id RETURN n` (direction
      "in" = nodes pointing AT node_id; "out" = nodes node_id points at).
- [ ] **Novel call sites migrate** (≥4): chapter_report,
      render_manuscript, list_chapters, novel_progress use
      `ctx.neighbors(novel_id, "CHAPTER_OF")`; scene listing uses
      `SCENE_OF`.
- [ ] **Music call sites migrate** (the 4 AlbumClaim scan sites) — or
      explicitly deferred with a row note if the claim nodes lack edges
      (they may be intent-scoped by design; verify before migrating).
- [ ] **Behaviour-preserving**: results identical to the scan+filter on
      all existing tests (the 250+ novel+music tests are the net).
- [ ] **Doctrine note** in CAPABILITY-AUTHORING: "declare an edge ⇒
      traverse it via ctx.neighbors; a write-only edge is dormant
      surface" (extends the dormant-surface audit heuristic).
- [ ] Drift check + TODO.md row.

## Design notes

- This is an ENGINE edit (capability.py) — the one spec in this wave
  that crosses the drop-in-capability bar, justified because the gap
  is what FORCES caps to bypass edges. Smallest possible surface: one
  method, no new node types, no wire-contract change.
- Keep `find()` untouched; neighbors is additive.

## Open questions

1. Should `neighbors` paginate (limit param)? (Recommend: yes,
   `limit=100` default — same shape as analyze.graph.)

## Followup

(Populated when the PR ships.)
