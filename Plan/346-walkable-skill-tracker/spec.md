---
spec_id: "346"
slug: walkable-skill-tracker
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 3]
depends_on: ["018", "026", "161", "290", "338", "343", "345"]
domain: lifecycle
wave: program-master
parent_spec: "338"
---

# Spec 346 — Walkable-skill tracker (skills as state machines)

> Child of the Lifecycle-pillar deep program (Spec 338). Owner directive: *"a
> tracker that tracks walkable skills."* Realizes CORE.md's "a skill IS a Lifecycle
> of ordered Phases" on the generic state-machine substrate (345): every walkable
> skill derives a `skill:<name>` machine, every `SkillRun` is a lifecycle on it,
> and the **tracker** is the single board of what walks exist, what's in flight,
> and where each one is.

## Why

CORE.md + `agency/skill.py` already say a skill is "a Lifecycle of ordered Phases"
— but the SkillRun walker hand-rolls position (count of `Phase` nodes) and lives
*outside* the Lifecycle substrate. So there is **no unified view** of walkable
skills: `skills.find` lists the catalogue, `skills.index` promotes Skill+Phase
nodes, `develop.skill_walk` walks one, a hard gate pauses at `input-required` — but
nothing tracks *all* in-flight walks, their current phase, what's blocked, or where
to resume. Spec 343's `lifecycle-management` discipline wants exactly this board.
Once 345 makes lifecycle generic, a skill is just a machine, and the tracker falls
out for free.

## Design

### A walkable skill derives a `skill:<name>` machine (built on 345)

`skills.index` already promotes a skill to `Skill` + ordered `Phase` nodes
(`HAS_PHASE`/`PRECEDES`). 346 derives a **machine** from that phase graph:

```
machine "skill:tdd":
  initial: "red"
  states:  ["red","green","refactor","verify","paused","done"]   # phases + paused + done
  transitions: red->[green,paused], green->[refactor,paused], refactor->[verify,paused],
               verify->[done,paused], paused->[<the phase it paused at>]
  terminal: ["done"]
```

Derivation is mechanical from `PRECEDES` order (no hand-authoring — rule 2). A
hard-gate phase adds a `paused` edge (the `input-required` analogue for the skill
machine); `resume` (343 / `SkillRun.resume`) is `move(paused → <phase>)`.

### SkillRun becomes a lifecycle on its skill machine

`develop.skill_walk(name)` opens `ctx.lifecycle.open(machine="skill:<name>")`;
each phase `submit` is a `move(→ next phase)`; a hard-gate pause is `move(→paused)`;
`resume_from` is `move(paused → <phase>)`. The `Skill`/`Phase` provenance nodes
(Spec 018/026) stay — the machine adds the *state* spine the walker lacked, so the
walk's position is the lifecycle `state`, not an inferred count.

### The tracker — three views (read surface on `manage` + `skills`)

The "tracker" is a read projection (no new write surface), composing the
Memory-pillar read-API:

| View | Source | Answers |
|---|---|---|
| **catalogue** | `skills.find` + the derived machine shape | which walkable skills exist, their phases/gates |
| **live board** | `lifecycle.find(machine LIKE "skill:%")` + `manage.state` | every in-flight walk, its current phase, paused/blocked, resume point |
| **history** | completed `skill:` lifecycles + their `Phase`/SkillRun provenance | what was walked, outcomes, where walks stall most (Spec 161 ranking input) |

Surfaced as `manage.skills_board()` (or `skills.tracker()` — a read verb on an
existing member cap, NOT a new capability) rendering the Spec 292 board Document.
The dogfood loop-detector + 343's stall detection consume the live board (a walk
stuck in `paused`/a phase past a threshold is a stall — reusing 344's events).

### What this slice does NOT do

- No new walker — `develop.skill_walk`/`SkillRun` stay; they open/move on the
  skill machine instead of hand-rolling position.
- No new capability — the tracker is read verbs on `manage`/`skills`.
- No change to skill authoring — machines are *derived* from the existing phase graph.

## Acceptance (Gherkin)

```gherkin
Scenario: a walkable skill derives a machine from its phase graph
  Given the "tdd" skill with phases red->green->refactor->verify
  When its skill machine is derived
  Then machine "skill:tdd" has initial "red" and terminal "done"
  And red->green is a legal transition but red->verify is not

Scenario: a skill walk is a lifecycle on the skill machine
  When I walk the "tdd" skill
  Then a lifecycle opens with machine "skill:tdd" in state "red"
  And submitting the red phase moves it to "green"

Scenario: a hard-gate pause is a move to paused, resumable
  Given a skill walk paused at a hard gate
  Then the lifecycle state is "paused"
  And resume moves it back to the paused phase

Scenario: the tracker live board lists in-flight walks with their phase
  Given two skill walks in flight at different phases
  When I read the tracker live board
  Then both appear with their current phase and resume point

Scenario: the catalogue lists available walkable skills with machine shape
  When I read the tracker catalogue
  Then every skills.find entry appears with its phases
```

## Followup — Implementation Status (2026-06-20)

Not started — opened by the owner's "tracker that tracks walkable skills" directive.
Derives a `skill:<name>` machine per walkable skill (from the Spec 026 phase graph),
makes `SkillRun` a lifecycle on it (position = state, not inferred count), and adds
the three-view tracker as read verbs on `manage`/`skills` (catalogue · live board ·
history). Builds on 345 (generic machines) + 343 (`SkillRun.resume`). No new
capability, no new walker.
