---
spec_id: "240"
slug: scene-writer-llm-loop
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "130"
depends_on: ["130", "220", "145", "147"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_scene_writer_loop.py
---

# Spec 240 — scene-writer iterate-to-gate loop

## Why

Spec 130 ships the 5-phase walkable + Spec 220 lands the production
TextDriver. The walk currently makes ONE generate pass + one check
pass; if checks fail the agent re-runs the walk manually. With Spec
145's preflight + 220's wet generate, the walk can iterate bounded N
times to gate-passing prose — the managed-Outcome iterate pattern from
the `claude-api` skill applied to scene authoring.

## Done When

- [ ] **`scene-writer(iterate=N) -> SceneWriteResult`** where
      `SceneWriteResult = {scene_id, final_artefact_id, iterations: int,
      gate_history: list[GateResult], stop_reason: Literal["passed",
      "budget","no_progress"], total_tokens: int}`. Invariant:
      `iterations <= N` AND `len(gate_history) == iterations`.
- [ ] **Convergence invariant** — `stop_reason="passed"` REQUIRES
      `gate_history[-1].passed is True`; any other stop_reason carries
      `gate_history[-1].passed is False` plus the failing-gate list.
- [ ] **Monotone progress, not pinned count** — invariant: across
      consecutive accepted iterations, the failing-gate count strictly
      decreases OR the loop short-circuits with
      `Codes.SCENE_NO_PROGRESS`. The test asserts the inequality
      `gate_history[i].failing > gate_history[i+1].failing`, never
      `iterations == 2`.
- [ ] **Each iteration records an Artefact** + diff; provenance shows
      the iteration path. Invariant: `final_artefact_id` is reachable
      from `scene_id` via a PRODUCES chain of length `iterations`
      (Spec 235 typed-path verifies).
- [ ] **Optional Managed-Agents Outcome path** (claude-api skill) —
      gates as gradeable rubric. Invariant: managed-path and inline-path
      return IDENTICAL SceneWriteResult shape; only `driver_kind` field
      differs.
- [ ] **Failed iterations → Reflections** (Spec 150 dogfood loop) —
      invariant: every iteration with `passed=False` emits exactly one
      Reflection node with `scope="scene_writer_iterate"`, back-pointer
      to the gate run, and the failing-gate names; recurrent patterns
      classify into amendment proposals.
- [ ] **Failure modes** — Driver unavailable mid-loop →
      `Codes.DRIVER_UNAVAILABLE`, partial iterations preserved as
      Artefacts (no rollback); token budget exhausts →
      `stop_reason="budget"` with the last artefact returned (not
      discarded); preflight (Spec 145) fails → loop NEVER starts,
      `Codes.PREFLIGHT_FAILED` returned with the missing inputs named.
- [ ] Test: a scene that fails on iteration 1 passes on 2 (mocked).
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  scene_id S with a brief, mocked Driver that produces prose
        failing 3 gates on pass 1 and 0 gates on pass 2
When:   scene_writer(S, iterate=5) runs
Then:   result.stop_reason == "passed" AND
        result.iterations == 2 AND
        result.gate_history[0].failing == 3 AND
        result.gate_history[1].failing == 0 AND
        result.gate_history[0].failing > result.gate_history[1].failing
        (monotone progress, asserted as INEQUALITY) AND
        a PRODUCES chain of length 2 exists from S to final_artefact_id

Given:  same scene, Driver keeps producing prose with 3 failing gates
When:   scene_writer(S, iterate=5) runs
Then:   result.stop_reason == "no_progress" AND
        Codes.SCENE_NO_PROGRESS recorded AND
        a Reflection emitted per failing iteration (Spec 150)
```

## Interconnects

- Spec 220 (wet generate) · Spec 145 (preflight) · **LLM-driver** (147).
- **Dogfood-loop chain** (150).
- Spec 237 (scene-brief cache) — every iteration shares the brief
  prefix; cache hits keep iterate cost bounded.
- Spec 232 (editorial judge) — judged findings inform revision prompt
  but never block the gate.
- Spec 241 (character-knowledge extract) — phase 5 of the walk; runs
  after `stop_reason="passed"`.
- Spec 230 (storyform completion) — same iterate-to-rubric pattern.

## Failure modes

LLM/remote/cache surfaces: Driver timeout mid-iteration, cache eviction
between iterations (cache hits degrade gracefully — re-prime on next
call), managed-agent outcome scoring returns malformed JSON (treat as
failing-gate, log `Codes.OUTCOME_PARSE_FAILED`, continue loop).

## Open questions

1. **Default N.** **Recommend:** 3 — pattern parity with Spec 230
   (5 is too costly per-scene; 3 catches the long tail).
2. **Revision strategy.** Full rewrite vs targeted edit per failing
   gate? **Recommend:** targeted edit on iterations 1-2, full rewrite
   on iteration 3 — preserves cache hits early.
3. **Outcome rubric source.** Hand-authored or derived from gates?
   **Recommend:** derived from the failing-gate list — single source
   of truth, no drift between rubric and gates.
