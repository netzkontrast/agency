---
spec_id: "222"
slug: novel-catalogue-graph-query
status: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "106"
depends_on: ["106", "203", "146", "154", "160", "217", "218", "221"]
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
surface + the output budget so a wrapping LLM driver never eats the
manuscript when it asked for a catalogue page.

## Done When

- [ ] **Catalogue queries route through `analyze.graph_query`** (Spec
      203) — cross-work relational questions in one call; no Python
      post-filter on a `find(label)` scan (the Spec 125 anti-pattern).
- [ ] **List verbs honor the output budget** (Spec 146/154 prefix +
      overflow capture + Spec 160 `--fields`).
- [ ] **Typed return shape**:
      ```python
      CatalogueQueryResult = {
        "prefix": {                       # cache-stable per author scope
          "author_id":          str,
          "schema_version":     str,
          "capability_set_hash": str,
        },
        "body": {
          "query":              str,       # the graph_query expression
          "rows":               list[dict], # `--fields`-projected
          "total":              int,
          "shown":              int,
          "edges_traversed":    list[str], # which Spec 203 edges fired
          "overflow_handle":    str | None,
          "next_cursor":        str | None,
        },
      }
      ```
- [ ] **Invariant — declared edges are traversed, not scanned.** For
      every cross-work query, assert `len(body.edges_traversed) >= 1`
      AND a grep of the verb impl finds zero `find(label="Scene")` +
      Python-filter sites. The catalogue uses Spec 203's `neighbors`
      surface (CLAUDE.md dormant-edge audit applied).
- [ ] **Invariant — prefix byte-stability per author scope.** Two
      catalogue queries with the same `author_id` and no work mutation
      return byte-identical `prefix`; `usage.cache_read_input_tokens >
      0` on the second call.
- [ ] **Invariant — overflow threshold RELATIONAL.** Assert
      `overflow_handle is not None` whenever rendered body bytes
      exceed the configured cap; never pin a row count.
- [ ] **Invariant — `--fields` projection strictness.** Every row in
      `body.rows` has keys ⊆ requested fields; unknown field raises
      `Codes.FIELDS_UNKNOWN`.
- [ ] **Invariant — author scoping.** A query with
      `author_id=A` MUST NOT return rows whose lineage edges end at a
      work owned by `author_id=B`; CI asserts via a 2-author fixture.
- [ ] **Failure modes**:
      - `Codes.GRAPH_QUERY_INVALID` propagated from Spec 203 when the
        expression names a non-existent edge — surface the typo;
      - `Codes.OVERFLOW_HANDLE_MISSING` for stale handles (Spec 154 GC);
      - `Codes.FIELDS_UNKNOWN` for an unknown projection key;
      - `Codes.AUTHOR_SCOPE_VIOLATION` if the impl somehow returns a
        row outside the requested author scope (a hard invariant —
        the catalogue is a privacy boundary).
- [ ] Test: a cross-work motif query returns the expected subgraph; a
      large listing captures-and-recalls; author-scope violation is
      detected; declared-edge traversal asserted via dormant-edge audit.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  an author with 4 novels totaling 280 chapters, where 6 scenes
        across 3 novels carry the codex tag "betrayal"
When:   catalogue_query("Scene WHERE tags contains 'betrayal' SERVES
        Novel WHERE author_id=A", fields=["title","novel_title","wc"])
        is called
Then:   body.rows length == 6
        AND every row has keys exactly {"title","novel_title","wc"}
        AND body.edges_traversed contains "Scene-SERVES-Novel" and
            "Novel-OWNED_BY-Author"
        AND no row's novel_title belongs to a different author
        AND a second identical call hits prefix cache

Given:  a catalogue listing of every scene across the 4 novels (~1100
        scenes, > MAX_BODY_BYTES projected)
When:   catalogue_query("Scene SERVES Novel WHERE author_id=A") is
        called
Then:   body.overflow_handle is a recall key
        AND recall_overflow(handle, grep="Chapter 12") returns the
            matching scenes across all 4 novels in stable order

Given:  catalogue_query passing fields=["nonexistent_key"]
When:   the verb runs
Then:   returns Codes.FIELDS_UNKNOWN naming the offending field
        AND does NOT silently project an empty dict
```

## Failure modes

The Spec 154 overflow store is external state — handle GC mid-session
surfaces `OVERFLOW_HANDLE_MISSING`. Spec 203 graph-query parse failures
propagate as `GRAPH_QUERY_INVALID` rather than silently returning empty.
Author scope is a privacy boundary, not a performance hint —
`AUTHOR_SCOPE_VIOLATION` is a fatal CI gate, never a soft warning.
Prefix cache reliance depends on byte-stability; a metadata change
(e.g. capability_set_hash bump) legitimately invalidates the cache and
that's expected — the invariant asserts stability ONLY when no mutation
happened.

## Interconnects

- Spec 203 (graph query) · **output-budget** (146/154/160).
- Spec 217 (build walkable) — the catalogue is the cross-build moat
  the walkable populates.
- Spec 218 (lifecycle output-budget) — the catalogue's prefix/body
  envelope is the same one lifecycle list verbs use.
- Spec 219 (storyform LLM-assist) — cross-work storyform queries route
  through this surface.
- Spec 220 (prose driver wet) — cross-work prose queries traverse the
  same Scene SERVES Novel moat.
- Spec 221 (research fan-out) — cross-work source-reuse queries
  ("every source cited by ≥ 2 of my novels") use this surface.
- Part of the novel provenance moat (Goal 2).

## Open questions

1. Per-author or global catalogue? **Recommend**: per-author scope by
   default (the owner edge); a shared-world catalogue is a Slice-2.
2. Should the prefix include the work count? **Recommend**: no — a
   new work mutates the prefix and kills the cache; keep
   author_id + schema_version + capability_set_hash only.
3. Cross-author queries for collab works? **Recommend**: defer — when
   needed, add an `AUTHORED_BY` edge to support multi-author works;
   the v1 single-owner edge is enough for the solo-novelist case.
4. Should `body.edges_traversed` include traversal counts?
   **Recommend**: yes — surfaces accidental scans (a count of 1 on an
   edge that should be many is a hint of `find(label)`+Python-filter
   regression).
