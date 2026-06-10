---
spec_id: "167"
slug: analyze-architecture-networkx-impl
status: draft
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

## Done When

- [ ] **`analyze.architecture` axis** computes the import graph via
      networkx: A001 cycles, A004 fan-out, A005 fan-in, A006
      god-module (LOC × fan-in).
- [ ] **Metrics are relationships, not snapshots** (rule 8) — the gate
      compares to a derived baseline, never a pinned count.
- [ ] **`[analyze]` extra gains networkx** (warm-recommend; silent
      fallback when absent, Spec 050 pattern).
- [ ] **Spec 157 gate consumes A001** — a new cycle fails CI.
- [ ] Test: an injected cycle is detected; fan-in/out match a fixture
      graph.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 157 (architecture gate) is the primary consumer.
- Spec 166 (extras expansion) is the sibling analyzer addition.
- **Drift-derivation chain** (149): baseline derived.

## Open questions

1. god-module threshold? **Recommend**: relative (top-decile fan-in ×
   LOC), not absolute — survives repo growth.
