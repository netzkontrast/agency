---
spec_id: "248"
slug: plural-character-graph-query
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "138"
depends_on: ["138", "203", "235", "216", "244", "146", "149"]
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

- [ ] **`query_phobia_cycles(system_id) -> CycleSet`** + **`query_co_front(
      system_id, pair_kind="max"|"adjacent"|"any") -> CoFrontSet`** —
      typed returns `CycleSet{cycles: list[{alter_ids: list[AlterId],
      length: int, weight: float}], system_id, computed_at}` and
      `CoFrontSet{occurrences: list[{scene_id, alter_ids: list[AlterId],
      pair_kind, violates_canon: bool}], system_id}`. All queries route
      through `analyze.graph_query` (Spec 203) — never bespoke scans.
- [ ] **Invariant: queries are pure graph walks** — no Python
      post-filter on a foreign-key prop while the PHOBIA_OF edge sits
      idle (the CLAUDE.md dormant-edge anti-pattern). Test:
      `grep`-style audit on the query module asserts zero
      `find(label)+filter` patterns; every alter relationship goes via
      `ctx.neighbors(node_id, edge)`.
- [ ] **`switching_log` derived as typed path** (Spec 235) — the log is
      a query over CoFront + Scene.timestamp ordering, never a
      hand-maintained list. Relationship:
      `len(switching_log) == count(co-front edges traversed)`.
- [ ] **Invariant: recognition discipline preserved across queries** —
      no query result EVER returns alter-label strings to the
      consumer; recognition stays on the substrate (Spec 138 + 216).
      Property test asserts `all(isinstance(r, AlterId) for r in
      result.alter_ids)` — IDs, never labels.
- [ ] **Invariant: max-pair derivation is computed** — "max-pair" is
      defined as `max(phobia_weight)` across the alter system, NOT a
      pinned literal pair. Test asserts the max-pair query result
      changes when a higher-weight PHOBIA_OF edge is added.
- [ ] **Recognition check (138) uses Spec 216 shared substrate** when
      216 ships — the recognition is one query module, used by both
      novel.plural-character and codex.character-sheet.
- [ ] **Failure modes**: missing PHOBIA_OF edges → query returns empty
      `CycleSet`, NOT error (an alter system with no conflicts is
      legal); cyclic PHOBIA_OF with self-loop → cycle reported with
      `length=1` (signal, not crash); query over a system_id with no
      alters → `Codes.SYSTEM_UNKNOWN` (Spec 151); large alter system
      (>50 alters) → query is cursored via the envelope (Spec 146)
      and obeys `MAX_PREFIX_TOKENS`.
- [ ] Test: a max-pair co-fronting query returns the offending scenes
      AND identifies which canon rule (Spec 247) is violated; PHOBIA_OF
      cycle of length 3 detected on a fixture.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a CharacterSystem with 5 alters; PHOBIA_OF edges form a
        triangle A→B→C→A (weight 0.9 each); a scene where A and C
        co-front (the max-pair by weight); a canon rule (Spec 247
        Lock) forbids max-pair co-fronting in chapter 1
When:   query_phobia_cycles(system_id) and query_co_front(system_id,
        pair_kind="max") run via analyze.graph_query
Then:   CycleSet.cycles contains [A,B,C] with length=3, weight=0.9;
        CoFrontSet.occurrences contains the scene with violates_canon=
        True; the switching_log derived via Spec 235 records the A→C
        transition; recognition check (138) sees only AlterIds in the
        result — never name strings; the violation feeds Spec 247
        approval workflow as a flag, not a Lock
```

## Interconnects

- Spec 203 (graph query) — the substrate; ALL queries route here.
- Spec 235 (typed paths) — switching_log + PHOBIA_OF traversal are
  declared edges, traversed via `ctx.neighbors` (Spec 125 doctrine).
- Spec 216 (shared name-exposure) — recognition substrate is shared
  with codex.character-sheet.
- Spec 244 (LLM voice-profile derive) — alter voice profiles inform
  PHOBIA_OF weights; this spec's queries reveal whether voice-derived
  weights produce realistic conflict topology.
- **Output-budget chain** (146) — large query results obey envelope
  body cap; per-system prefix is cacheable.
- **Drift-derivation chain** (149) — query verb list re-derives from
  the registry; new query auto-appears in docs.

## Open questions

1. **Cycle reporting granularity.** Surface all cycles or only minimal
   ones? **Recommend**: minimal by default (no cycle that is a
   superset of another), with `?include_supersets=true` flag — the
   minimal set is the actionable signal; supersets are derivable.
2. **Pair-weight tie-breaks.** If two pairs share max weight, return
   all or pick one? **Recommend**: return all — "max-pair" is a SET,
   not a singleton; the canon rule (Spec 247) decides what to do
   with ties.
3. **Recognition check at query layer or consumer layer?**
   **Recommend**: query layer — the substrate guarantees the
   discipline; consumers cannot forget to apply it. Spec 216 codifies.
