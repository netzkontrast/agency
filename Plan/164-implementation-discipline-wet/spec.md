---
spec_id: "164"
slug: implementation-discipline-wet
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "041"
depends_on: ["041", "081", "156", "147"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/develop/_main.py
  - tests/test_implementation_discipline_wet.py
---

# Spec 164 — Implementation-discipline skills, wet phases

## Why

Spec 041 (implementation-discipline-skills) is Partial — 3 disciplines
ported (dispatching-parallel-agents, subagent-driven-development,
executing-plans) under the derive model, but the skills are scaffolds
the agent fills in chat. With Spec 147 + 156's wet path, the
disciplines can RUN their checks — e.g. `executing-plans` can verify a
plan step's acceptance via the Driver, `subagent-driven-development`
can score a returned subagent transcript.

## Done When

- [ ] **Each discipline gains an optional wet verify phase** — gated on
      `[anthropic]`, degrades to the scaffold prompt.
- [ ] **`develop.execute` (executing-plans) verifies step acceptance**
      via a structured-output Driver call before advancing the walk.
- [ ] **The literal skills/ folders fully retired** behind the 080/081
      derive model (041's standing cleanup).
- [ ] Test: a plan step whose acceptance fails halts the walk (mocked
      Driver); derive-model parity asserted.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · **dogfood-loop chain** (150 via
  Reflections from failed verifies).
- Spec 156 (wet pressure) is the sibling wet-path spec.

## Open questions

1. Verify every step or only gate steps? **Recommend**: gate steps only
   (cost); intermediate steps stay scaffold-checked.
