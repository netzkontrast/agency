---
spec_id: "238"
slug: story-time-graph-query
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "128"
depends_on: ["128", "203", "131", "235"]
vision_goals: [2]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_story_time_query.py
---

# Spec 238 — story-time graph query

## Why

Spec 128 ships StoryTimeEvent + NarrativeBeat + 6 verbs. Many
continuity questions are RELATIONAL ("every event the POV witnessed
before chapter 12", "events HAPPENS_AT a time the antagonist was
elsewhere") — exactly what Spec 203 + Spec 235 typed-paths serve. This
wires story-time onto the moat-query surface.

## Done When

- [ ] **Story-time queries via `analyze.graph_query`** (Spec 203) —
      multi-hop through HAPPENS_AT / REVEALED_IN / PRECEDES. Return
      shape: `StoryTimeQueryResult = {events: list[StoryTimeEvent],
      beats: list[NarrativeBeat], paths: list[Path], coverage: float}`
      where `coverage = events_visited / total_events_in_scope`.
- [ ] **`narrative_order` derived as typed path** (Spec 235) instead of
      ad-hoc lex sort — invariant: for every consecutive pair
      `(e_i, e_{i+1})` in the returned order, a PRECEDES edge exists
      directly OR transitively (verified via `neighbors_path`). No
      property-sort fallback.
- [ ] **POV knowledge intersection** (Spec 131) composable in one query —
      invariant: `events_pov_witnessed(C, before=beat_id)` returns the
      INTERSECTION of `{e : C WITNESSES e}` and `{e : e PRECEDES
      beat_id}`; the cardinality relation `|witnessed| <= |all_events|`
      holds.
- [ ] **Continuity invariant** — invariant: no returned event has both
      HAPPENS_AT(t) and PRECEDES(e') where e' HAPPENS_AT(t' < t); the
      query SURFACES temporal contradictions, never silently sorts
      around them. Contradictions returned in `result.contradictions`.
- [ ] **Failure modes** — empty scope (no events in range) → empty
      result, `coverage == 1.0` by convention (vacuous truth);
      conflicting PRECEDES cycle → `Codes.TEMPORAL_CYCLE` naming the
      cycle node-ids; missing POV character → `Codes.UNKNOWN_CHARACTER`.
- [ ] Test: cross-event relational queries return expected subgraph.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  5 StoryTimeEvents E1..E5, character C witnesses {E1, E3, E5},
        chapter 12 corresponds to beat B12 with E4 PRECEDES B12
When:   events_pov_witnessed(C, before=B12)
Then:   result.events == [E1, E3] AND
        result.coverage == 2/3 (the 3 C-witnessed events, 2 before B12)
        AND every event in result has a PRECEDES path to B12

Given:  E2 HAPPENS_AT t=10 and E3 PRECEDES E2 but E3 HAPPENS_AT t=15
When:   story_time_query runs over E2, E3
Then:   result.contradictions includes (E3, E2) AND
        Codes.TEMPORAL_CYCLE is NOT raised (PRECEDES isn't a cycle, just
        a contradiction) — author sees the inconsistency surfaced
```

## Interconnects

- Spec 203 (graph query) · Spec 235 (typed paths).
- Spec 131 (character knowledge) for POV intersection.
- Spec 233 (worldbuilding Slice 2) — PlantedElement firing time is a
  story-time query against FIRED_IN.
- Spec 241 (character-knowledge extract) — extracted KnownFacts join
  the witnessed-set via LEARNED_IN edges queried here.

## Open questions

1. **PRECEDES transitivity.** Materialize transitively or compute on
   query? **Recommend:** compute on query via `neighbors_path` (Spec
   235) — avoids stale materialization when beats are reordered.
2. **POV granularity.** Per-character or per-character-per-beat?
   **Recommend:** per-character with optional beat-scope filter; the
   beat filter composes via PRECEDES.
3. **Contradiction policy.** Surface and continue, or raise?
   **Recommend:** surface in `result.contradictions` — the query is
   read-only diagnostic; gates (Spec 233) decide whether to block.
