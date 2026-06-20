---
spec_id: "344"
slug: lifecycle-transition-events
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 3]
depends_on: ["021", "076", "156", "338", "339", "340"]
domain: lifecycle
wave: program-master
parent_spec: "338"
---

# Spec 344 — Lifecycle transition events (the "lifecycle Events" gap)

> Child of the Lifecycle-pillar deep program (Spec 338). Closes the gap a
> codegraph deep-analysis pass surfaced (Spec 338 §Why item 6): a lifecycle
> **transition records nothing**, so observers can only poll `state`. This slice
> makes every `lifecycle.move` (Spec 339/340) **emit a typed transition event**,
> recorded on the existing `Event` substrate — the foundation the observe suite
> (341) consumes instead of polling.

## Why

The codebase already has a rich event ecosystem, but **lifecycle state changes
are absent from all of it** (Spec 338 §Why item 6, verified via codegraph):

- `Event` nodes — `engine.dispatch_hook` (Spec 076) records one per Claude Code
  hook event, linked `OBSERVED_DURING` the active `AGENCY_INTENT`.
- `LoopEvent` — `agency/_loop_events.py` (Spec 156), a typed loop-detection
  record; Slice 2 writes `Event{name:"loop_detected"}` via the hook handler.
- `MonitorEvent` — `agency/_monitor.py` (Spec 021), the engine SLOG channel
  (`server_start`/`server_stop`; `jules.verify` emits `silent_fail_detected`).

But `lifecycle.move`/`complete`/the unguarded `update` sites write `state` and
**emit nothing**. The consequences are the N4 need in Spec 338:

- `manage.whats_next`/`state` must **re-scan** every Lifecycle serving an intent
  to know what changed.
- `jules.watch` **polls** sessions on a timer.
- the dogfood loop-detector reads `Event`s but can never see a stall (a lifecycle
  stuck in `input-required`) because no event marks the transition.
- the **transition history is unrecoverable** — you can only infer it from `Gate`
  edges, and a plain `submitted→working→completed` run leaves no trail at all.

Goal 3 ("one recovery flow", "no special-casing per agent") needs observers to
see *every* agent's transitions uniformly. That requires the transition itself to
be a first-class, recorded event — not a side effect a poller might notice.

## Design — `move` emits, the `Event` substrate records

### The typed shape (`agency/_lifecycle_events.py`, mirroring `_loop_events.py`)

```python
@dataclass(frozen=True)
class LifecycleEvent:
    """Typed lifecycle-transition record (mirrors LoopEvent, Spec 156)."""
    event_id:    str
    lifecycle_id: str
    from_state:  str
    to_state:    str
    intent_id:   str
    at:          str
    evidence:    str = ""
```

A pure, engine-free dataclass (like `LoopEvent`) so tests/doctor/audit can build
and assert one without an engine.

### Emission — folded into `move` (Spec 339), zero new call sites

`lifecycle.move` (the SOLE state writer, Spec 339) — after the transition guard
(340) passes and the `state` is written — records the event on the **existing
`Event` node type** (rule 2 — no new node type; reuse Spec 076):

```
Event{name:"lifecycle_transition", lifecycle, from, to, intent, at}
  -[:OBSERVED_DURING]-> Intent        # the Spec 076 edge, already enforced
  -[:OBSERVED_DURING]-> Lifecycle     # so watch(lifecycle_id) finds its own trail
```

Because emission lives in `move`, and 339 routes the three former unguarded
writes through `move`, **every** state change — including a gate's
`→input-required` and a dispatch child's `working→…` — emits an event *for free*.
No capability adds an emit call.

> **Reuse, not a new event system.** The `Event` node + `OBSERVED_DURING` edge +
> `dispatch_hook` recording path already exist (Spec 076). This slice records a
> new *kind* of Event (`name:"lifecycle_transition"`), exactly as Spec 156's
> loop-detector records `name:"loop_detected"`. The `MonitorEvent` SLOG channel
> (Spec 021) is ALSO emitted for terminal/blocked transitions (`completed`,
> `failed`, `input-required`) so a session sees them on the monitor without
> reading the graph — mirroring how `jules.verify` already emits
> `silent_fail_detected`. (Capture is full — CLAUDE.md #76; no truncation.)

### Consumption (what 341 + others read)

- `lifecycle.watch(lifecycle_id)` (341) returns the ordered `lifecycle_transition`
  Event trail for that lifecycle — no poll.
- `manage.timeline` (Spec 290) already orders Events for an intent; the transition
  events now appear there automatically (they `OBSERVED_DURING` the intent).
- the dogfood loop-detector gains stall/loop visibility over transition events.

### What this slice does NOT do

- No new node type — reuses the Spec 076 `Event` + `OBSERVED_DURING`.
- No new emit call sites — emission is inside `move` only.
- No polling daemon — `watch` (341) reads the recorded trail; the only existing
  poller (`jules.watch`) is unchanged here (341 composes it).

## Acceptance (Gherkin)

```gherkin
Scenario: every move emits a transition event
  Given an open Lifecycle in state "submitted"
  When I call lifecycle.move(lid, to_state="working")
  Then an Event{name:"lifecycle_transition", from:"submitted", to:"working"} exists
  And it is OBSERVED_DURING the serving intent and the lifecycle

Scenario: a gate pause emits a transition event for free
  Given a Lifecycle serving the current intent
  When a gate fails (routing through lifecycle.move(→input-required))
  Then a lifecycle_transition Event to "input-required" exists
  And a MonitorEvent for the blocked transition is emitted

Scenario: the transition trail is recoverable without polling
  Given a Lifecycle moved submitted→working→completed
  When I read its OBSERVED_DURING events in order
  Then the full transition history is present (no inference from Gate edges)

Scenario: transitions appear in the intent timeline
  Given transitions recorded for a lifecycle serving an intent
  When I call manage.timeline(intent_id)
  Then the lifecycle_transition events appear in order
```

## Followup — Implementation Status (2026-06-20)

Not started — opened by the codegraph deep-analysis pass (Spec 338 refinement).
Adds `agency/_lifecycle_events.py` (typed `LifecycleEvent`, pure) + emission folded
into `lifecycle.move` (reusing the Spec 076 `Event` node + Spec 021 monitor
channel). Build-order: lands after 340 (so transitions are guarded before they are
broadcast) and before 341 (which consumes the trail).
