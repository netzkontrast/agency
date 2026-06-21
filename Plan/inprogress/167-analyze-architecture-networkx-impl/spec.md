---
spec_id: "167"
slug: analyze-architecture-networkx-impl
status: draft
state: inprogress
last_updated: 2026-06-10
owner: "@agency"
enhances: "051"
depends_on: ["051", "157", "166", "149"]
vision_goals: [4]
affects:
  - agency/capabilities/analyze/_architecture.py  (NEW)
  - tests/test_analyze_architecture.py
---

# Spec 167 — analyze-architecture networkx implementation

## Why

Spec 051 (analyze-architecture-networkx) is Not Started — it scopes
networkx-driven A001 cycle refactor + A004 fan-out / A005 fan-in / A006
god-module metrics. It is the metric engine the architecture-drift gate
(Spec 157) needs. Implementing it lights both.

## Done When (measurable invariants — rule 8)

- [ ] **Typed metric shape: `ArchMetric{axis_id, kind: Literal["cycle",
      "fan_out", "fan_in", "god_module"], nodes: list[str], score:
      float, baseline: float}`** — every metric returns the same
      envelope.
- [ ] **Invariant: A001 cycle count is monotonically non-increasing**
      across PRs — gate fails if the new cycle set ⊄ baseline cycle
      set (relationship, not pinned count).
- [ ] **Invariant: fan-out + fan-in computed from the SAME graph** —
      `sum(fan_out) == sum(fan_in)` over the import graph (edge-count
      identity, derived).
- [ ] **Invariant: god-module threshold is RELATIVE** — top-decile of
      `fan_in × LOC`, computed per-run from the live tree (survives
      repo growth, never pinned).
- [ ] **Invariant: when networkx missing, axis returns `[]` + doctor
      hint** (Spec 050 silent fallback).
- [ ] **Relationship: Spec 157 gate's failing finding equals at least
      one A001 cycle** — the gate's evidence pointer resolves to an
      ArchMetric node.
- [ ] **Failure mode (graph build):** an unresolvable import (typo,
      missing module) does NOT crash the build — the offending edge
      becomes a `dangling` node in the graph + emits
      `Codes.IMPORT_UNRESOLVED`; partial metrics still flow.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  baseline has 0 import cycles; a developer adds an import in
        agency/capabilities/foo/_main.py that creates foo → bar → foo
When:   `analyze run --axis A001` runs in CI
Then:   returns ArchMetric{kind="cycle", nodes=["foo","bar"], score=2,
        baseline=0}; gate fails with evidence pointing at the new
        cycle (cycle_set ⊄ baseline_set)

Given:  baseline cycles = {(foo,bar)}; PR removes one but adds (baz,qux)
When:   gate runs
Then:   gate FAILS — the new cycle is not in the baseline, even though
        the total count is unchanged (set discipline, not count)

Given:  PR removes (foo,bar) and adds NO new cycles
When:   gate runs
Then:   gate PASSES + the baseline is re-derived as {} (monotone shrink
        is allowed; baseline never frozen)
```

## Failure modes

| Failure | Analyzer response |
|---|---|
| networkx missing | silent `[]` + doctor hint (Spec 050) |
| Import unresolvable | `dangling` node + `IMPORT_UNRESOLVED` Reflection; partial metrics flow |
| Gate flake (graph build non-deterministic) | Spec 169 flake gate catches; build re-run |
| god-module set shifts on repo growth | acceptable — threshold is relative, not pinned |
| A001 baseline drift (someone edits the stored baseline) | Spec 149 drift gate fails — baseline derives, never hand-set |

## Interconnects

- Spec 157 (architecture gate) is the primary consumer of A001.
- Spec 166 (extras expansion) is the sibling analyzer addition;
  semgrep's A007 + networkx's A001/A004/A005/A006 share the registry.
- Spec 172 (registry expansion proof) gates the analyzers' coexistence.
- Spec 169 (CI coverage + flake) protects against non-deterministic
  graph build.
- Spec 170 (doctor) reports `networkx_available` + the live A-axis set.
- **Drift-derivation chain** (149): baseline derived per-run, never
  pinned snapshot.
- Spec 151 (Codes coverage) supplies `IMPORT_UNRESOLVED`.

## Open questions

1. god-module threshold? **Recommend**: relative (top-decile fan-in ×
   LOC), not absolute — survives repo growth (rule 8).
2. Baseline storage — file or graph node? **Recommend**: graph node
   (BaselineSnapshot SERVES Spec 157, PRODUCED_BY the gate run) —
   queryable, audit-friendly, doctrine rule 2.
3. Cycle-detection algorithm — strongly-connected components or
   simple-cycles? **Recommend**: SCC for the gate (O(V+E), faster on
   large graphs); simple-cycles for the report (richer detail, opt-in).

## Followup — Implementation Status (Slice 1, 2026-06-12)

**Verdict:** Slice 1 SHIPPED on `claude/autonomous-completion` as part of
the wave-1 typed-shape batch-2 (intent:2219e694; engine-driven tdd walk).

### Done — Slice 1 (typed shape)

Typed frozen dataclass + `__post_init__` invariants in
`agency/_typed_shapes_wave1_part2.py`; tests in
`tests/test_typed_shapes_wave1_part2.py` (17 tests total across the
8-spec batch). Slice 2 wires each shape into its consuming runtime
(red-team rerunner, CLI projection, derive audit, wrapper modules,
networkx metric, axis registry, migration walker, ref audit).

### Still — Slice 2+

See the spec's main "Done When" + "Still" sections.

