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
      invariants against the live tree:
      - exactly three wire verbs exposed (`search`/`get_schema`/`execute`),
      - every `capabilities/<name>/` is import-isolated (no
        `from agency.capabilities.<other>` except via `ctx`),
      - the four-concept node set is present + closed.
- [ ] **Spec 051 metrics wired** — networkx cycle/fan-in/fan-out feed
      an `analyze.architecture` axis; the gate fails on a NEW cycle
      (compared to a derived baseline, not a pinned count — rule 8).
- [ ] **CI job** runs it on every PR.
- [ ] Test: an injected cross-capability import trips the gate.
- [ ] TODO row + drift clean.

## Interconnects

- **Drift-derivation chain** (149): the architecture baseline is
  derived, not pinned.
- Spec 051 (networkx) is the metric engine.
- Spec 042 (analyze) hosts the new axis.

## Open questions

1. Block on any new cycle, or only god-module/fan-in regressions?
   **Recommend**: block on cross-capability import + wire-verb-count
   (hard invariants); warn on metric regressions (tunable).
