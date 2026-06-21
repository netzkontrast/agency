---
spec_id: "210"
slug: music-catalogue-graph-query
status: draft
state: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "097"
depends_on: ["097", "203", "146", "154", "207", "212", "206"]
vision_goals: [2, 1]
affects:
  - agency/capabilities/music/_main.py
  - agency/capabilities/music/clusters/catalogue.py
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
      Typed return: `CatalogueQuery = {nodes: list[NodeRef], edges:
      list[EdgeRef], next_cursor: str | None, recall_handle: NodeId | None,
      query_provenance: NodeId}`.
- [ ] **List verbs honor the output budget** (Spec 146/154) — shared
      `ListResult` shape with Spec 207 lifecycle lists.
- [ ] **The deferred `clusters/catalogue.py` split lands** (094-family
      migration); existing `db_init` becomes a rendered view backed by
      the graph (rule 2 of CLAUDE.md applied to the music store).
- [ ] **Query provenance** — every catalogue query lands a
      `Query SERVES intent` node + an `Artefact RESULT_OF Query` edge so
      audits can replay any historical answer.
- [ ] **Test**: a relational catalogue query returns the expected
      subgraph; a large listing captures-and-recalls; the rendered
      `db_init` view stays read-equivalent to the graph projection.
- [ ] **TODO row + drift clean.**

## Measurable invariants (relationships, not pinned counts)

- **Graph-query equivalence** — for every pre-Spec-210 catalogue verb
  (e.g. `list_albums_released(year)`), the new `analyze.graph_query`
  path returns a `CatalogueQuery` whose `nodes` set equals the legacy
  verb's result set (golden test runs both paths).
- **Render-view consistency** — `db_init` view rows == graph projection
  rows for the same query, every commit (Spec 149 derived-doc check
  extends here).
- **Cursor stability** — paging through a 1000-album catalogue with
  `limit=50` returns each album EXACTLY once; no duplicates, no skips
  (test asserts `set` equality and `len == 1000`).
- **Provenance for every query** — `assert count(Query SERVES intent) ==
  count(query_calls)` over a test run; the moat covers reads too.

## Worked example (Given/When/Then)

```text
Given:  300 catalogue rows; 12 albums released in Q1 2026; 9 passed the
        audio-release gate
When:   analyze.graph_query("tracks on albums released in Q1 2026
        WHERE audio_release.passed == True")
Then:   returns CatalogueQuery with nodes containing exactly the 9
        albums' tracks (set equality with the legacy verb's result)
        AND query_provenance is a graph node SERVING the caller intent
        AND next_cursor=None (under budget) OR recall_handle≠None (over)
        AND a second identical call's envelope.prefix is byte-identical
```

## Failure modes (Nygard)

| Failure | Verb response |
|---|---|
| Query syntax invalid | typed `Codes.QUERY_PARSE_ERROR` with a column/operator hint; never silently return empty |
| Result exceeds `MAX_BODY_TOKENS` (Spec 154) | emit `next_cursor` + `recall_handle`; never partial without a recall |
| Backing graph offline | typed failure; do NOT fall through to the legacy `db_init` view (consistency would silently drift) |
| Render-view drift detected (graph != db_init view) | doctor raises; install-time lint fails until reconciled |
| Cursor invalidated by mid-paging mutation | typed `Codes.CURSOR_STALE`; caller restarts from the start (idempotent) |

## Interconnects

- Spec 203 (graph query) · **output-budget** (146/154).
- Spec 207 (lifecycle list-budget) — shares the `ListResult` shape and
  cursor encoding.
- Spec 212 (music research fan-out) — citations land on catalogue
  nodes; this verb returns them.
- Spec 206 (produce-album walk) consumes catalogue queries when
  resolving "every asset SERVING the album".
- The catalogue is part of the music provenance moat (Goal 2).

## Open questions

1. Keep `db_init` SQLite or fold into the graph? **Recommend**: the
   graph IS the store (Goal 7) — `db_init` becomes a rendered view;
   defer the migration to a Slice-2 if it risks the shipped surface.
2. Query language surface? **Recommend**: reuse Spec 203's surface
   directly; music adds no domain DSL (the drop-in bar — coupling
   would be the bug).
3. Cache the rendered `db_init` view? **Recommend**: lazy-rebuild on
   write; readers see graph truth; cache invalidation is a write-edge
   trigger, not a TTL.
