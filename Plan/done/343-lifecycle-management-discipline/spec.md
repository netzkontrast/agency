---
spec_id: "343"
slug: lifecycle-management-discipline
status: shipped
state: done
last_updated: 2026-06-21
owner: "@agency"
vision_goals: [2, 4, 9]
depends_on: ["018", "078", "081", "290", "338", "339", "341"]
domain: lifecycle
wave: program-master
parent_spec: "338"
---

# Spec 343 — The `lifecycle-management` walkable discipline + phases/resume

> Child of the Lifecycle-pillar deep program (Spec 338). The **capstone**: it
> makes Lifecycle management a *walkable discipline* (CORE.md: a skill IS a
> Lifecycle template — so the discipline that manages lifecycles is itself a
> Lifecycle, the recursion the canon names), and closes the phase/resume surface
> so `skill_walk` is understood as a Lifecycle projection.
>
> **Pillar + panel notes (2026-06-20).** Since Lifecycle is a *pillar* (no
> `lifecycle` cap), the discipline is a **skill contributed by a member cap** — it
> homes on `manage` (the Memory-pillar read-API it orchestrates) or a `home=
> "lifecycle"` member, not a `lifecycle` capability. `resume` is a thin
> substrate/`ctx.lifecycle` method, not a new cap verb. **Panel C-1 (ownership):**
> the discipline may `move` lifecycles serving *sub-intents* of the session's
> intent, but not lifecycles under an unrelated intent tree — the move asserts the
> target SERVES the active intent's chain (the `gate.check` SUPERSEDED_BY-aware
> guard precedent). **Hi-1 (stall detection):** surfacing a lifecycle stuck in
> `input-required`/`verify` is a phase-1 `manage` query over the 344 events (a
> transition older than a threshold with no successor) — owned here, not a daemon.

## Why

Spec 338 §thesis item 5: the pillar is complete when **one walkable discipline**
drives it, orchestrating the existing `manage` reads + the new frame verbs (339–342)
— not a new pile of verbs. Two loose ends remain after 339–342:

1. **No discipline.** Intent got `guided-discovery` (Spec 323); the Capability
   pillar has `authoring-capabilities`; Lifecycle has no walkable skill that takes
   an agent from "what's in flight?" through "advance it / unblock it / close it"
   against acceptance. The `manage` reads answer *what*; nothing walks the *do*.

2. **Phases & resume are half-owned.** `develop.skill_walk` (`develop/_main.py:1097`)
   walks a Skill's `Phase`s (`HAS_PHASE`/`PRECEDES`, ontology.py:33-34) — and CORE.md
   says "a skill = an ordered Lifecycle of Phases". But there is no `lifecycle.resume`
   that re-enters a paused (`input-required`) lifecycle at its current phase, and the
   phase↔state relationship is implicit. This slice makes it explicit: a phased skill
   run IS a Lifecycle, and resuming it is a `move(input-required → working)` at the
   recorded phase.

## Design

### The `lifecycle-management` walkable discipline (`skills` slot, Spec 078/081)

A static, walkable skill (delivered one phase at a time via
`develop.skill_walk`, Spec 018) — orchestrating EXISTING verbs, ~zero new code
(the 307 refinement lesson — the discipline is the surface, not new verbs):

| Phase | Verb(s) it runs | Output |
|---|---|---|
| 1. survey | `manage.open_intents` + `lifecycle.find(state="working"/"input-required")` | the board: what's in flight, what's blocked |
| 2. triage | `manage.whats_next(intent)` per blocked lifecycle | the blocker per lifecycle (gate / input / dependency) |
| 3. unblock | `lifecycle.move(input-required → working)` / `lifecycle.check` resolve | each blocked lifecycle advanced or escalated |
| 4. advance | `lifecycle.move(→ next state)` per active lifecycle | progress recorded against acceptance |
| 5. close | `lifecycle.close(outcome)` + `gate.check` (done-gate) | terminal lifecycles closed; acceptance verdict |
| 6. report | `manage.render` → the `lifecycle-board.md` Document | the board rendered as a file peer (Spec 292) |

The skill is **derived** from its module docstring (Spec 080 derivability) and
records its own `SkillRun` provenance (Spec 018) — the recursion made literal: the
discipline that manages lifecycles runs *as* a Lifecycle.

### `lifecycle.resume` (the phase/state bridge)

```python
@verb(role="act")
def resume(self, lifecycle_id: str) -> dict:
    """Re-enter a paused lifecycle. Asserts the lifecycle is in
    input-required | auth-required (the only resumable states, per 340's
    table), moves it →working, and returns the recorded phase so the
    caller re-enters skill_walk at that phase (resume_from=).
    Returns {lifecycle_id, state, phase, resume_from}."""
```

`resume` is the typed bridge between the Lifecycle state machine (340) and the
phase walker. The codegraph analysis confirmed the walker side is **already
shipped**: `agency/skill.py::SkillRun.resume` (Spec 018) reconstructs the walker's
position from the append-only graph — the count of recorded `Phase` nodes IS the
next index — and a hard-gate pause already returns `resume_from` = the **phase
NAME** + the `produces` to supply (`skill.py:159-165`). So `lifecycle.resume` does
NOT duplicate the walker: it asserts the lifecycle is resumable (340's table:
`input-required | auth-required`), does the `move(→working)`, and returns the
`phase` so the caller calls `SkillRun.resume(...)` / `develop.skill_walk(
resume_from=phase)`. It is the *state* half (the transition) bolted to the
*walker* half (already there). This closes CORE.md §3's "Gates = input-required →
Intent re-entry": a gate failure (341 `check`) is a guarded `move(→input-required)`
that emits a transition event (344); `resume` is the only legal exit, re-entering
the walker at the recorded phase after the Intent re-entry resolves the blocker.

### Phase↔state made explicit (documentation + one helper)

The relationship "a skill run is a Lifecycle; its current `Phase` is recorded on
the Lifecycle's `phase` prop" is already half-true (`Lifecycle.phase`,
ontology.py:26). This slice adds `_base._phase_of(lifecycle_id)` (read the current
phase) + the reference doc (`references/state-machine.md` §phases) making the
projection explicit — no new node type (the `Phase`/`HAS_PHASE` ontology already
exists; we connect, not invent).

### What this slice does NOT do

- No new walker — `develop.skill_walk` (Spec 018) stays the walker; `resume` feeds
  its `resume_from`.
- No new verbs beyond `resume` — the discipline orchestrates 339–342 + `manage`.
- No FastAPI surface (deferred, Spec 338 §"Scoped OUT").

## Acceptance (Gherkin)

```gherkin
Scenario: the discipline walks the whole pillar over existing reads
  Given several in-flight lifecycles, one blocked on a gate
  When I walk the lifecycle-management discipline
  Then phase 1 surveys them via manage + lifecycle.find
  And phase 3 unblocks the gated lifecycle via lifecycle.move
  And a SkillRun provenance record exists for the walk

Scenario: resume re-enters a paused lifecycle at its phase
  Given a Lifecycle in "input-required" recorded at phase "implement"
  When I call lifecycle.resume(lid)
  Then it moves to "working" and returns resume_from="implement"
  And skill_walk(resume_from="implement") picks up there

Scenario: resume refuses a non-resumable state
  Given a Lifecycle in "completed"
  When I call lifecycle.resume(lid)
  Then it raises (only input-required | auth-required are resumable)

Scenario: the board renders as a file peer
  When phase 6 runs manage.render scoped to lifecycles
  Then lifecycle-board.md is written with the in-flight board
```

## Followup — Implementation Status (2026-06-21)

**SHIPPED** (branch `claude/lifecycle-343`). The capstone — the Lifecycle pillar is
complete: write frame (339) · enforced machine (340) · observe suite (341) ·
parameterization (342) · **discipline (343)**.

A prior pass had landed a thin STUB (the skill registered as a bare literal, a
`pass` walk test, no board); this slice brings it to a real ship.

**Done:**
- **The `lifecycle-management` walkable discipline** (`manage.ontology.skills`,
  home=`memory` — the Memory-pillar read-API it orchestrates). Six phases —
  `survey → triage → unblock → advance → close → report` — each carrying a
  non-binding `runs` hint naming the verbs the agent invokes (cross-cap:
  `manage.*` · `lifecycle.resume`/`move`/`advance`/`close` · `gate.check` ·
  `document.mirror`). It is a GUIDE (the walker steps phases; the agent
  orchestrates), so `develop.skill_walk("lifecycle-management", …)` genuinely
  walks to completion and records its own **`Skill` provenance** — the recursion
  made literal (managing lifecycles runs AS a lifecycle). The stub's ugly
  formatting + glued `_phase_of`/class were cleaned.
- **`lifecycle.resume`** (the phase/state bridge, already on the substrate from
  339): asserts the lifecycle is `input-required`/`auth-required` (340's only
  resumable states), `move(→working)`, returns `phase`/`resume_from` so the caller
  re-enters `develop.skill_walk(resume_from=…)`. It is the state half bolted to the
  shipped walker half (`SkillRun.resume`, Spec 018) — no walker duplication.
- **The board as a Spec 292 file peer (phase 6 / acceptance §4).** New
  `document.render` scope `lifecycle-board` (`_render.render_lifecycle_board`:
  H1 + a by-state count table + an in-flight table of `id · state · machine ·
  parameterization · intent` over the non-terminal lifecycles). Phase 6 runs
  `document.mirror(scope="lifecycle-board", apply_path="lifecycle-board.md")` —
  the canonical graph→file projection with the `agency-node:` anchor + a
  graph-sourced `DocRevision` (keep-both), reusing the 292 machinery rather than
  re-rolling a writer.
- **`_phase_of(ctx, lifecycle_id)`** reads the current phase (the projection made
  explicit; no new node type — `Phase`/`HAS_PHASE`/`Lifecycle.phase` already exist).

**Tests:** 4 acceptance scenarios in `features/lifecycle_management.feature` — the
discipline genuinely walks the six named phases + records `Skill` provenance;
`resume` re-enters at the recorded phase; `resume` refuses a terminal state; the
report phase writes `lifecycle-board.md` with the in-flight board + the file-peer
anchor. lifecycle-management + document + lifecycle + manage (90) green; drift +
no-truncate clean; install regen no-diff (no new verbs — only a render scope +
discipline metadata).

**Not done (out of scope per §"What this slice does NOT do"):** no new walker
(reuses `develop.skill_walk`); no auto-bound cross-cap phase execution (the
discipline is a guide); no FastAPI surface (Spec 338 §"Scoped OUT").
