---
spec_id: "240"
slug: scene-writer-llm-loop
status: draft
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

- [ ] **`scene-writer(iterate=N)`** runs generate → check → revise up
      to N times until gates pass or budget exhausts.
- [ ] **Each iteration records an Artefact** + diff; provenance shows
      the iteration path.
- [ ] **Optional Managed-Agents Outcome path** (claude-api skill) —
      gates as gradeable rubric.
- [ ] **Failed iterations → Reflections** (Spec 150 dogfood loop).
- [ ] Test: a scene that fails on iteration 1 passes on 2 (mocked).
- [ ] TODO row + drift clean.

## Interconnects

- Spec 220 (wet generate) · Spec 145 (preflight) · **LLM-driver** (147).
- **Dogfood-loop chain** (150).
