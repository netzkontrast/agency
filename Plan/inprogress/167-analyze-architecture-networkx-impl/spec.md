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

- [x] **Typed metric shape: `ArchMetric{axis_id, kind, nodes, score,
      baseline}`** — `baseline` added (additive default); every metric
      returns the same envelope. `derive_arch_metrics` populates it.
- [ ] **Invariant: A001 cycle count is monotonically non-increasing**
      across PRs — DEFERRED: needs a per-merge baseline cycle-set stored
      in CI (the cross-PR gate); not fakeable offline.
- [x] **Invariant: fan-out + fan-in computed from the SAME graph** —
      `sum(fan_out) == sum(fan_in)` (edge-count identity).
      `test_fan_out_equals_fan_in_edge_identity` + `fan_identity_holds`.
- [x] **Invariant: god-module threshold is RELATIVE** — top-decile of
      `fan_in × LOC` computed per-run, never pinned.
      `test_god_module_threshold_is_relative_not_pinned`.
- [x] **Invariant: when networkx missing, the pure-Python fallback still
      yields metrics + doctor reports the backend** — the analyzer's
      `_HAS_NX` fallback; `arch_metrics_summary` reports `networkx`.
- [ ] **Relationship: Spec 157 gate's failing finding equals an A001
      cycle** — DEFERRED with the cross-PR gate above (the cycle metrics
      ARE the analyzer's A001 findings, but the gate wiring is CI-side).
- [x] **Failure mode (graph build):** `Codes.IMPORT_UNRESOLVED` defined;
      `arch_metrics_summary` reports it on a build failure (partial
      metrics still flow; the build never crashes the doctor).
- [x] TODO row + drift clean.

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

### Done — Slice 2 partial (2026-06-26)

The typed-metric deriver + the offline-derivable invariants are shipped:

- `agency/_arch_metrics.py`:
  - `derive_arch_metrics(root=None)` — composes the architecture analyzer
    (`analyze/_architecture.py` — `_build_graph` / `_scc_cycles` / `_cycle_path`
    / `_degrees`) into typed `ArchMetric`s (cycle / fan-out / fan-in /
    god-module). No second graph build (rule 2). Live: 545 metrics, 5 cycles,
    20 god-modules.
  - `fan_identity_holds(metrics)` — the `sum(fan_out)==sum(fan_in)` edge identity.
  - `arch_metrics_summary(root=None)` — `{ready, metrics, cycles, god_modules,
    networkx}`; `ready` iff the identity holds; never raises.
- `ArchMetric` gained `baseline` (additive default).
- `Codes.IMPORT_UNRESOLVED` added.
- `agency_doctor.architecture_metrics` consumes the summary.
- 5 invariant tests in `tests/test_arch_metrics.py` (all green).

### Still — deferred (needs CI runtime)

- **A001 cycle-count monotonicity gate across PRs** + **Spec 157 evidence-pointer
  relationship** — both need a per-merge baseline cycle-set stored CI-side; not
  fakeable offline. The cycle metrics themselves ARE the analyzer's A001
  findings; only the cross-PR gate wiring remains.

**Verdict:** PARTIAL — the typed deriver + identity + relative-threshold +
networkx-fallback + IMPORT_UNRESOLVED shipped; the cross-PR cycle gate is the
remaining slice.

