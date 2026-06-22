---
spec: 287
title: develop-plan-execute-skill
status: Implementing (Slice 1 shipped)
state: inprogress
depends_on: [018, 025, 040, 285]
clusters: [lifecycle, meta]
vision_goals: [1, 3, 7]
---

<!-- doc-source: agency/capabilities/develop/_main.py -->

# Spec 287 — develop `plan-execute` discipline (plan-authoring → execution-with-checkpoints)

> Owner request (PR #141 comment 4698453381): a first-class
> *plan-authoring → plan-execution-with-checkpoints* discipline in the
> `develop` cluster, inspired by superpowers (`writing-plans`,
> `executing-plans`, `subagent-driven-development`, `brainstorming`) and
> superclaude (`sc-workflow`, `sc-task`, `sc-spawn`, `sc-estimate`).

## Why

`develop` had `plan` (a single `map` phase) and `execute` (load/execute/
checkpoint/verify) — thin, and the plan lived nowhere as provenance. The gap:
a single walkable discipline that **authors a bite-sized plan, gates on
sign-off, executes step-by-step with review checkpoints**, and records the
plan **as graph nodes** (rule 2) rather than a parsed markdown file.

## Design (agency-native constraints)

- **Walkable Lifecycle template** (goal 3) — walked via `develop.skill_walk`,
  one phase at a time; the engine delivers a phase, pauses at hard gates.
- **Plan is graph provenance, not a file** (rule 2 / goal 7) — `draft_plan`
  mints a `Plan` + `PlanStep` nodes SERVING the intent (`HAS_STEP` edges);
  the plan markdown renders on demand (Spec 283 substrate later).
- **Token-efficient execution** (goal 1) — the execute-step phase cues
  `delegate.dispatch_decision` (Spec 040, 11 signals): delegate vs. inline.
- **Hard gates** = plan sign-off + per-run checkpoint + final synthesis
  (the elicit/pause mechanism from Spec 018/285).

### The discipline — `plan-execute`
| # | phase | produces | gate | note |
|---|---|---|---|---|
| 1 | `frame` | requirements | — | cues `intent.decompose`/`assumptions` |
| 2 | `draft-plan` | plan | — | **bound** → `develop.draft_plan` (mints Plan+PlanStep) |
| 3 | `plan-signoff` | user_confirmed | **hard** | never execute an unapproved plan |
| 4 | `execute-step` | step_results | — | cues `delegate.dispatch_decision` |
| 5 | `checkpoint` | reviewed | **hard** | review checkpoint (re-plan or continue) |
| 6 | `synthesize` | summary | **hard** | close the Plan; link artefacts |

(Bound phases carry a single `produces` key — the walker puts the verb result
into `produces[0]`; Spec 025 contract.)

### Verbs (on `develop`)
- `draft_plan(title, steps)` — act. `steps` = JSON list or newlines → `Plan` +
  one `PlanStep{index,description,state:pending}` per step. Returns
  `{plan_id, step_ids, count}`.
- `record_step_outcome(step_id, outcome, evidence)` — act. `outcome` ∈
  {done,blocked,skipped}; bi-temporal `state`/`evidence` update.
- `plan_status(plan_id)` — transform. Traverses `HAS_STEP` (declared ⇒
  traversed) → `{title, status, steps:[…], complete}`.

### Ontology (on `develop`)
`Plan{title}` (+ optional status), `PlanStep{plan,index,description}` (+ state,
evidence), edge `HAS_STEP`, enum `PlanStep.state ∈ PLAN_STEP_STATES`.

## Tests (RED → GREEN)
`tests/test_develop_plan_execute.py` — 8 tests: draft mints Plan+steps (+SERVES,
+newline form), record_step_outcome (state update + bad-outcome guard),
plan_status (roll-up + completion), skill registered with the 3 hard gates +
bound draft-plan, and a walk that runs draft-plan for real then pauses at
plan-signoff. All green.

## Followup — Implementation Status (2026-06-13)
- **Status: Implementing — Slice 1 shipped.** The discipline, the three verbs,
  the ontology, and 8 tests are GREEN; install regenerated for the new
  `/agency-plan-execute` skill command.
- **Open (Slice 2, for Vision-owner review):** (a) single `plan-execute` vs. a
  `write-plan`/`execute-plan` pair (cross-session resumability); (b) reuse
  Spec-285 `requires_input`/`sample` on `execute-step` for assumption
  resolution; (c) a `render_plan(plan_id)` markdown view via the Spec 283
  substrate. Layout + open Qs mirrored in `refactor.md`.
