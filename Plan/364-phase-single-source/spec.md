---
spec_id: "364"
slug: phase-single-source
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [3]
depends_on: ["018", "363"]
parent_spec: "362"
domain: skills
---

# Spec 364 — Phase = single source (the walk surfaces instructions)

> Child 2 of Spec 362. Make the phase graph the ONE source that drives both the
> walk and the rendered file (A2), so a walked agent gets the same instructions a
> reader gets — no divergence, no "phase prose isn't surfaced" gap.

## Why
`SkillRun.current()` returns only `{index,name,produces,gate}` — the walking agent
never receives `goal`/`instructions`/`example`. So even when phases carry content
(363), the walk doesn't deliver it.

## Design (sketch)
- `SkillRun.current()` returns the phase's `goal`/`instructions`/`example`/`freedom`
  (from 363) alongside the structural fields.
- `develop.skill_walk` passes them through in its phase payload (the agent sees the
  instructions for the current rung).
- **Parity invariant + test:** the instructions a walk delivers for phase N ==
  the instructions the rendered SKILL.md shows for phase N (both read the same
  `skill.yaml`). A drift between them is a test failure.

## Slices (TDD)
1. `current()` + the walker return surface the content fields.
2. The walk↔file parity acceptance test (one source, two surfaces, equal content).

## Acceptance
- Walking a discipline delivers each phase's `instructions` (not just its name).
- The parity test passes: walk content == rendered content for every phase.
- A no-host / read-only agent can ignore the walk and read the same content inline.
