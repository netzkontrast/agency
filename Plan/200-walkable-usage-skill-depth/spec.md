---
spec_id: "200"
slug: walkable-usage-skill-depth
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "081"
depends_on: ["081", "152", "147", "146"]
vision_goals: [1, 4]
affects:
  - agency/_skilldoc.py
  - tests/test_walkable_usage_depth.py
---

# Spec 200 — walkable usage-skill depth (adaptive phase budgeting)

## Why

Spec 081 derives a `<cap>-usage` walkable skill per capability (verbs
clustered by role, ≤6 phases, hard confirm gate). The phase clustering
is currently static (by role). For a capability with many verbs, a
fixed ≤6-phase cap either crams or omits. With the Spec 147 Driver, the
derived walk can adapt its phase structure to the actual task the agent
states — pulling only the relevant verbs into the walk — while keeping
the per-phase token budget (Goal 1) and the hard gate.

## Done When

- [ ] **`<cap>-usage` walk accepts an optional task hint** — the Spec
      147 Driver selects + orders the relevant verbs into ≤6 phases for
      THAT task; degrades to the static role-clustering without
      `[anthropic]`.
- [ ] **Per-phase output stays within budget** (Spec 146/Goal 1) — one
      phase's instruction at a time.
- [ ] **The hard confirm gate is preserved** (Spec 081 doctrine).
- [ ] Test: a task hint produces a task-relevant phase order (mocked
      Driver); static fallback deterministic.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · **output-budget chain** (146).
- Spec 152 (typed Skill) is the phase type.

## Open questions

1. Adapt phases or just verb selection? **Recommend**: verb selection
   within fixed phase roles v1 (predictable); full phase synthesis later.
