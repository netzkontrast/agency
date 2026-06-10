---
spec_id: "156"
slug: wet-pressure-path-and-loop-hooks
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "011"
depends_on: ["011", "021", "076", "147", "155"]
vision_goals: [3, 6]
affects:
  - agency/_middleware/loop.py
  - agency/capabilities/thinking/_pressure.py
  - tests/test_wet_pressure.py
---

# Spec 156 — Wet pressure path + loop-hooks layer

## Why

Spec 011 shipped the agentic guardrails DRY — its Followup notes "Wet
pressure path + loop-hooks layer deferred (no LLM driver / no hook
layer in v1)". Both blockers are now lifted: Spec 147 gives the LLM
Driver, Spec 076 gives the unified hook layer. The deferred half can
land: pressure scenarios actually run an LLM through the discipline and
score whether it held; loop-detection fires a hook on a real
transcript.

## Done When

- [ ] **Wet `run_pressure_test`** — drives the Spec 147 Driver through a
      loaded scenario and `score_transcript`s the real output (not a
      fixture). Records a `Reflection(scope="pressure")`.
- [ ] **Loop-hook** — `_middleware/loop.py::detect_loop` wired to the
      Spec 076 hook dispatch so a detected loop emits an `Event` node +
      a `MonitorEvent` (Spec 021) the watcher surfaces.
- [ ] **The two discipline skills (agentic-pressure-test,
      orchestrator-discipline) gain a wet phase** — optional, gated on
      `[anthropic]`.
- [ ] Test: a looping fake-transcript trips the hook; a wet pressure run
      records a scored Reflection (mocked Driver in CI).
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147): the wet path's engine.
- Spec 076 (unified hooks) is the loop-hook substrate.
- Spec 021 (monitor channel) surfaces detected loops.
- Spec 155 (red-team) shares the pressure-scenario substrate.

## Open questions

1. Run wet pressure in CI (costs API tokens) or local-only?
   **Recommend**: local + tag-gated CI; the DRY scenario sweep stays
   the default CI gate.
