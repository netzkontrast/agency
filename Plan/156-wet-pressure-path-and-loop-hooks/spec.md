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
      fixture). Returns a typed `WetPressureResult{scenario_id: str,
      held: bool, score: float, transcript_id: NodeId,
      reflection_id: NodeId, duration_s: float, model: str}`. Records a
      `Reflection(scope="pressure")` linked to the transcript Artefact.
- [ ] **Loop-hook** — `_middleware/loop.py::detect_loop` wired to the
      Spec 076 hook dispatch so a detected loop emits an `Event` node +
      a `MonitorEvent` (Spec 021) the watcher surfaces. Typed
      `LoopDetectedEvent{intent_id, repeat_count, signature_hash,
      first_at, latest_at}`.
- [ ] **The two discipline skills (agentic-pressure-test,
      orchestrator-discipline) gain a wet phase** — optional, gated on
      `[anthropic]`.
- [ ] **Measurable invariants** (rule 8):
      (a) `wet_score >= dry_score - epsilon` per scenario — wet
      execution does NOT outperform the dry rubric by accident;
      anomalies surface as Reflections;
      (b) every detected loop emits exactly one Event node + one
      MonitorEvent (1:1, no double-fire, no swallow);
      (c) `loop_signature_hash` is stable across re-runs of the same
      transcript (deterministic signature, not wall-clock-keyed);
      (d) wet-pressure transcripts are SERVED by the originating
      intent — provenance closes the loop back to GOALS.md Goal 6.
- [ ] Test: a looping fake-transcript trips the hook; a wet pressure run
      records a scored Reflection (mocked Driver in CI).
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  pressure scenario "sunk_cost_pressure" (Spec 011 substrate)
        and `[anthropic]` installed
When:   run_pressure_test(scenario="sunk_cost_pressure", wet=True)
Then:   Driver runs the scenario; score_transcript returns 0.0..1.0;
        WetPressureResult{held=True, score=0.82, transcript_id="art_x",
        reflection_id="ref_y", model="claude-opus-4-7"};
        Reflection(scope="pressure") SERVES the originating intent

Given:  an agent transcript with a 4x repeated tool call signature
When:   _middleware/loop.detect_loop processes the next event
Then:   LoopDetectedEvent fires through Spec 076 hooks once;
        a MonitorEvent surfaces to the watcher; the originating intent
        is annotated with the loop signature for Spec 150 to ingest
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| API non-determinism inflates score variance | Driver temperature, transient quality drift | invariant (a) — wet/dry delta gate | record `model + sampling_seed`; run wet N times when CI-relevant |
| Hook double-fire on retried event | re-entrant detect_loop on retry | invariant (b) — 1:1 gate | idempotency key on Event node (signature_hash + intent_id) |
| Driver timeout swallows scenario | network / rate limit | typed `Codes.WET_PRESSURE_DRIVER_TIMEOUT` | fall back to DRY rubric + Reflection noting the skip |
| Cost blow-up on full suite | every PR runs wet | tag-gating + per-run token budget | local + tag-gated CI default (open question 1) |

## Interconnects

- **LLM-driver chain** (147): the wet path's engine.
- Spec 076 (unified hooks) is the loop-hook substrate.
- Spec 021 (monitor channel) surfaces detected loops.
- Spec 155 (red-team) shares the pressure-scenario substrate — red-team
  loads invariants; wet-pressure scores them with a live Driver.
- Spec 152 (typed Skill/Phase) is re-used to parse adversarial scenario
  dicts — single parse boundary across discipline surfaces.
- Spec 150 (dogfood classifier) ingests wet-pressure Reflections as
  amendment proposals — the loop closes back to spec edits.
- Spec 151 (Codes coverage) supplies `Codes.WET_PRESSURE_DRIVER_TIMEOUT`
  and `Codes.LOOP_DETECTED`.

## Open questions

1. Run wet pressure in CI (costs API tokens) or local-only?
   **Recommend**: local + tag-gated CI; the DRY scenario sweep stays
   the default CI gate.
2. Loop-signature granularity — tool name only, or tool+args hash?
   **Recommend**: tool+args hash (catches "same retry with same args";
   tool-name-only over-fires on legitimate poll loops).
