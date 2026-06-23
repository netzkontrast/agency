---
spec_id: "372"
slug: phase-single-source
status: done
state: done
last_updated: 2026-06-23
owner: "@agency"
vision_goals: [3]
depends_on: ["018", "371"]
parent_spec: "370"
domain: skills
---

# Spec 372 — Phase = single source (the walk surfaces instructions)

> Child 2 of Spec 370. Make the phase graph the ONE source that drives both the
> walk and the rendered file (A2), so a walked agent gets the same instructions a
> reader gets — no divergence, no "phase prose isn't surfaced" gap.

## Why
`SkillRun.current()` returns only `{index,name,produces,gate}` — the walking agent
never receives `goal`/`instructions`/`example`. So even when phases carry content
(371), the walk doesn't deliver it.

## Design (sketch)
- `SkillRun.current()` returns the phase's `goal`/`instructions`/`example`/`freedom`
  (from 371) alongside the structural fields.
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

## Followup — Implementation Status (2026-06-21)

**Slice 1 — SHIPPED (option A: minimal single-source; render-side parity deferred to 373).**

Done (file:line evidence):
- `agency/skill.py` — `phase()` builder gains the inline content kwargs
  (`goal`/`instructions`/`example`/`done_when`/`freedom`), inserted only when
  given so legacy 3-arg phase dicts stay byte-identical. `SkillRun.current()`
  surfaces those fields alongside the structural ones (empty string when a
  phase authored none) — the single source a walking agent reads (A2).
- `agency/capabilities/develop/_main.py` — `_skill_walk`'s `input-required`
  (hard-gate pause) payload now carries the paused phase's
  `goal`/`instructions`/`example`/`freedom` (from `current()`), so the agent
  sees WHAT to do at the rung, not just its name (A1/A2). The `tdd` discipline
  is the first inline-content exemplar (all four phases carry goal/instructions;
  red + verify carry an example; per-phase `freedom` R8 level).
- Tests: `tests/acceptance/features/skill_walk.feature` + `test_skill_walk.py`
  — 3 new scenarios: (1) a paused walk surfaces the current phase's
  instructions + goal; (2) the surfaced instructions equal the instructions
  authored on that phase (one source, two surfaces — read live, not
  snapshotted, rule 8); (3) progressive disclosure (`current()`) surfaces a
  non-gate phase's authored instructions from the one source. 14/14 skill_walk
  scenarios green; 95 passed across the walk/parse/v2/registry/generator/
  develop blast radius; `check-drift` clean (install regen diff-free — phase
  content is not rendered yet, so no install drift).

**Slice 2 — SHIPPED (render-side parity, the 373 hinge, now landed).** 373 Slice 2
shipped `emit_skill._render_phase_detail`, which renders each phase's
`goal`/`instructions` inline beneath its walk row from the SAME single source the
walker reads. The walk ↔ *rendered file* parity is realised + tested:
`tests/acceptance/test_render_substrate.py` asserts every instruction the walker
surfaces for a `tdd` phase appears verbatim in the rendered file (driven through
the live `SkillRun`, read live — rule 8). With Slice 1, 372's acceptance ("walk
content == rendered content for every phase") is fully met.

**Spec 372 COMPLETE.** The phase graph is the ONE source driving both the walk
(`SkillRun.current()` surfaces goal/instructions/example/freedom) and the rendered
file (`_render_phase_detail`); a walked agent and a reader get identical phase
content (A2).

Out of scope (noted, not a gap): auto-advanced (non-gate) phases are surfaced via
`current()` but not via the atomic walker's return (it pauses only at hard gates)
— a per-phase walk surface waits until a consumer needs it (option A).
