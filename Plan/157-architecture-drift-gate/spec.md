---
spec_id: "157"
slug: architecture-drift-gate
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "015"
depends_on: ["015", "051", "042", "149"]
vision_goals: [4, 6]
affects:
  - scripts/check-architecture
  - agency/capabilities/analyze/_main.py
  - tests/test_architecture_drift_gate.py
---

# Spec 157 — Architecture-drift gate

## Why

Spec 015 (architecture-review) was a one-time milestone that produced
the 017/018/019 promotions — a snapshot, not a standing check. Spec 051
(analyze-architecture-networkx, Not Started) would add cycle / fan-out /
god-module metrics. Together they should become a STANDING gate: the
documented architecture invariants (four concepts, three-verb wire
surface, capability-per-folder, no cross-capability imports except via
`ctx.registry`) are machine-checkable and CI fails on a violation.

## Done When

- [ ] **`scripts/check-architecture`** asserts the documented
      invariants against the live tree and returns a typed
      `ArchitectureReport{wire_verbs: list[str], import_violations:
      list[(src, dst, file, line)], cycles: list[list[str]],
      fan_in: dict[str, int], fan_out: dict[str, int],
      concept_set: set[str], drift_against_baseline: dict[str, int]}`:
      - exactly three wire verbs exposed (`search`/`get_schema`/`execute`),
      - every `capabilities/<name>/` is import-isolated (no
        `from agency.capabilities.<other>` except via `ctx`),
      - the four-concept node set is present + closed.
- [ ] **Spec 051 metrics wired** — networkx cycle/fan-in/fan-out feed
      an `analyze.architecture` axis; the gate fails on a NEW cycle
      (compared to a derived baseline, not a pinned count — rule 8).
- [ ] **CI job** runs it on every PR.
- [ ] **Measurable invariants** (rule 8):
      (a) `len(wire_verbs) == 3` AND `set(wire_verbs) == {"search",
      "get_schema", "execute"}` — hard CORE.md invariant;
      (b) `len(import_violations) == 0` — cross-capability imports
      route via `ctx.registry` only;
      (c) `len(cycles) <= baseline_cycles` (monotone non-increasing —
      adding cycles fails; removing them advances the baseline);
      (d) every node label in `concept_set` is one of Intent / Capability
      / Lifecycle / Memory (closed set, no silent additions);
      (e) `drift_against_baseline` derives from the LAST shipped report
      (stored as a Reflection), never a hand-pinned constant.
- [ ] Test: an injected cross-capability import trips the gate;
      an injected fourth wire verb trips the gate; baseline floor
      advances when a cycle is removed.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a refactor adds `from agency.capabilities.analyze import _internal`
        to agency/capabilities/research/_main.py
When:   scripts/check-architecture runs in CI
Then:   ArchitectureReport.import_violations contains
        ("research", "analyze", "research/_main.py", L42);
        exit 1; PR blocked with Codes.ARCHITECTURE_CROSS_CAPABILITY_IMPORT

Given:  a refactor removes an existing cycle (analyze → memory → analyze)
When:   scripts/check-architecture runs
Then:   len(cycles) < baseline_cycles; the script ADVANCES the baseline
        (writes a new Reflection); next PR's monotone floor is tighter
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Baseline races on parallel PRs | two PRs reduce cycles independently | invariant (e) derives baseline at CI time, not commit time | always compare against `main` snapshot, never local fixture |
| Dynamic import bypasses static check | `importlib.import_module("agency.capabilities.x")` | AST check covers literal `import` + `from`; flag `importlib` use in capabilities | warn on `importlib` in capability dirs; require `ctx.registry` |
| Wire-verb rename | shipped verb renamed without doctrine update | invariant (a) — frozen set | rename = additive (alias) per CORE.md; hard error otherwise |
| Concept-set drift | new node label added to ontology | invariant (d) — closed set audit | promote via Spec 016 doctrine; closed-set tests gate |

## Interconnects

- **Drift-derivation chain** (149): the architecture baseline is
  derived, not pinned.
- Spec 051 (networkx) is the metric engine.
- Spec 042 (analyze) hosts the new axis.
- Spec 151 (Codes coverage) is one of the standing invariants this gate
  asserts — supplies `Codes.ARCHITECTURE_CROSS_CAPABILITY_IMPORT`.
- Spec 153 (schema coverage) `coverage_fraction` is one of the standing
  monotone fields this gate enforces.
- Spec 155 (red-team) hook into the gate's CI surface — both run on
  every PR.
- Spec 159 (no-markdown-parse) is enforced as one of the architecture
  invariants the gate asserts.

## Open questions

1. Block on any new cycle, or only god-module/fan-in regressions?
   **Recommend**: block on cross-capability import + wire-verb-count
   (hard invariants); warn on metric regressions (tunable).
2. Where does the baseline live — file or graph Reflection?
   **Recommend**: graph Reflection (rule 2 — graph is the store);
   `scripts/check-architecture` reads the latest, writes a new one
   on advance, no file to merge-conflict.
