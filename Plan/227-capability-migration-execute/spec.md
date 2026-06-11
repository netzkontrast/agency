---
spec_id: "227"
slug: capability-migration-execute
status: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "111"
depends_on: ["111", "147", "182", "183", "149", "150", "226", "228"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/
  - tests/test_capability_migration.py
---

# Spec 227 — capability-migration plan execution

## Why

Spec 111 (capability-migration) is the PLAN — 17 existing caps + 2
in-flight domain caps mapped to the adoption surface + migration shape +
PR sequencing. A plan that isn't executed rots. The enhancement waves
(146-226) ARE much of the adoption the plan scoped (LLM-driver,
output-budget, derived docs); this spec reconciles the 111 plan against
what the waves shipped, executes the remaining migrations, and the
opportunity detector (Spec 183) surfaces caps that should adopt a verb
they're re-implementing. Without execution + a derived completion %,
111 stays Partial indefinitely — the moat is the *adopted* substrate,
not the planned one.

## Done When

- [ ] **Reconciliation report ships** as a typed return shape from
      `capability.migration_status()`:
      ```python
      MigrationStatus = {
        "total_caps":     int,                       # live from registry
        "migrated":       list[str],                 # cap names done
        "pending":        list[PendingMigration],    # ranked by 183
        "wave_credits":   dict[str, list[str]],      # wave_id -> caps
                                                     # already adopted
        "completion_pct": float,                     # derived; not pinned
      }
      PendingMigration = {
        "cap":            str,
        "reimplements":   list[str],   # substrate verbs duplicated
        "evidence":       list[str],   # file:line citations
        "priority":       Literal["high","medium","low"],
        "blocked_by":     list[str],   # spec ids
      }
      ```
- [ ] **Migration parity invariant** — for every cap in `migrated`, a
      table-driven test asserts pre- and post-migration behaviour is
      observably equivalent on a fixture intent (same Artefacts emitted,
      same Reflection count, no new failure modes). Drift from parity
      is a hard failure, not a warning.
- [ ] **Opportunity detector wired** (Spec 183) — `pending` is RANKED
      by re-implementation surface area (LOC duplicated × call-site
      count), not authored order. Invariant: the top-ranked pending
      migration's `reimplements` list is non-empty.
- [ ] **Cluster coherence (Spec 182) re-checked** post-migration — every
      migrated cap still maps cleanly to its Spec 047 cluster; no cap
      lands in two clusters; no cluster loses a member it depended on.
- [ ] **Failure modes** (touches cap mutation):
      `Codes.MIGRATION_PARITY_BROKEN` when the post-migration cap emits
      a different Artefact graph than pre-migration (rollback the PR);
      `Codes.SUBSTRATE_VERB_MISSING` when the target verb was renamed
      mid-flight (the detector points at the rename);
      `Codes.CLUSTER_DRIFT` when a migration moves a cap out of its
      declared Spec 047 cluster (requires explicit override).
- [ ] **111 row flips toward Shipped** with a DERIVED completion % —
      `migrated / total_caps` read live off `MigrationStatus`, not
      hand-authored. (Rule 8: invariants over magic numbers.)
- [ ] Test: a synthetic cap re-implementing `develop.test` is flagged by
      183, ranked first in `pending`, then migrated; the parity test
      passes; the cap's Artefact graph is byte-equal pre/post on a seeded
      intent.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  17 caps in registry; 11 already adopt the substrate verbs the
        146-226 waves shipped; 4 still re-implement helpers; 2 in-flight
When:   capability.migration_status() runs
Then:   returns MigrationStatus with migrated.len == 11,
        pending.len == 4, completion_pct ~= 11/17 (derived),
        pending[0].reimplements names a real substrate verb,
        wave_credits maps 146 -> [caps that adopted output-prefix]

Given:  a cap re-implements its own token counter (4-chars-per-token)
When:   the migration executes (substituting Spec 082 TokenCounter)
Then:   parity test passes (Artefacts byte-equal on fixture intent),
        the cap's token field now sources from the live counter,
        completion_pct increments by 1/total_caps (derived)

Given:  a migration accidentally moves a cap from cluster A to cluster B
When:   migration_status() runs post-merge
Then:   raises Codes.CLUSTER_DRIFT, names cap + both clusters,
        blocks the TODO row flip until the cluster delta is justified
```

## Failure modes (Nygard)

| Failure | Response |
|---|---|
| `MIGRATION_PARITY_BROKEN` | rollback PR; parity diff attached as Reflection |
| `SUBSTRATE_VERB_MISSING` | detector points at rename; spec amendment proposed via Spec 150 |
| `CLUSTER_DRIFT` | block flip; require explicit `cluster_override=True` |
| In-flight cap conflict | hold the migration until the in-flight spec ships |
| Empty `pending` despite re-implementation | 183 detector tuning escalates to Reflection |

## Interconnects

- Spec 183 (opportunity detector) ranks the migrations.
- Spec 182 (cluster coherence) validates the result.
- Spec 149 (derived docs) reads `completion_pct` for the 111 row + TODO roll-up.
- Spec 147 (LLM driver) is the migration target for caps re-implementing
  one-off LLM shims (Spec 026's `llm_select` precedent).
- Spec 150 (dogfood-loop classifier) surfaces re-implementation patterns
  as amendment proposals — pending migrations feed the loop.
- Spec 226 (thinking cap Slice 2) is itself a migration target — the
  intent-cap thin-wrapper move is one row in `pending`.
- Spec 228 (dossier cap) consumes the migrated research-substrate verbs.

## Open questions

1. Big-bang or incremental? **Recommend**: incremental, one cap per PR
   (the 111 sequencing) — the waves already proved the pattern, and
   per-PR rollback is cheap.
2. **Parity test grain.** Artefact-graph equality or behavioural? **Recommend**:
   both — Artefact-graph equality is the structural invariant; a
   behavioural fixture-intent assertion catches semantic regressions
   the graph shape misses.
3. **In-flight cap handling.** Migrate before or after their Slice 1?
   **Recommend**: after — `pending` carries `blocked_by` pointing at
   the in-flight spec id; the detector skips them until ship.
4. **Completion-% denominator.** Total caps, or only caps with a
   substrate-adoption opportunity? **Recommend**: the latter — a cap
   with zero re-implementation surface is trivially "migrated"; the
   denominator should reflect real work, not registry bloat.
