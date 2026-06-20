---
spec_id: "343"
slug: lifecycle-management-discipline
status: draft
last_updated: 2026-06-20
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
phase walker (`develop.skill_walk`'s `resume_from`, already shipped). It does not
duplicate the walker — it returns the `phase` so `skill_walk(resume_from=phase)`
picks up where the pause happened. This closes CORE.md §3's "Gates = input-required
→ Intent re-entry": a gate failure (341 `check`) pauses at a phase; `resume`
re-enters at that phase after the Intent re-entry resolves the blocker.

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

## Followup — Implementation Status (2026-06-20)

Not started — capstone slice. Adds the `lifecycle-management` walkable discipline
(orchestrating 339–342 + `manage`, ~zero new verbs) and `lifecycle.resume` (the
phase/state bridge to `develop.skill_walk`). Completes the Lifecycle pillar: write
frame (339) + enforced machine (340) + observe suite (341) + parameterization
(342) + discipline (343).
