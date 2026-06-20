---
spec_id: "344"
slug: lifecycle-transition-events
status: partial
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

### Emission — folded into substrate `move`, split by transition class (panel B4)

> **The B4 decision: do NOT graph-record every transition.** Spec 336 (SHIPPED)
> moved high-volume capture OFF the graph precisely because `Event`s were ~95% of
> `session.db` bloat. A graph `Event` per `move` (per child, per retry) would
> re-introduce it. So 344 **splits by transition class**:
>
> | Transition class | Sink | Why |
> |---|---|---|
> | **terminal/blocked** (`→completed·failed·canceled·input-required·auth-required`) | durable graph **`Event`** | low-volume, real provenance ("the state it reached") |
> | **intermediate churn** (`submitted→working`, `working→verify`) | the Spec 021 **monitor channel** (`MonitorEvent`) | high-volume telemetry, not provenance — never hits the graph |

`agency/lifecycle.py::Lifecycle.move` (the SOLE state writer) — after the guard
(340) passes and `state` is written — emits via `_emit_transition`:

```
# terminal/blocked → durable graph Event (reuse Spec 076 node + edge):
Event{name:"lifecycle_transition", lifecycle, from, to, intent, at}
  -[:OBSERVED_DURING]-> Intent
  -[:OBSERVED_DURING]-> Lifecycle
# intermediate churn → monitor only (no graph node):
engine.monitor.emit(MonitorEvent(source="lifecycle", kind="transition", ...))
```

Because emission lives in substrate `move`, and 339 routes every former unguarded
writer through it, **every** state change emits *for free* (no capability adds an
emit call) — but only the load-bearing ones become durable graph provenance.

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
Scenario: intermediate churn goes to the monitor, NOT the graph (panel B4)
  Given an open Lifecycle in state "submitted"
  When I call lifecycle.move(lid, to_state="working")
  Then NO graph Event node is recorded for submitted→working
  And a MonitorEvent{source:"lifecycle", kind:"transition"} is emitted

Scenario: a terminal/blocked transition is durable graph provenance
  Given a Lifecycle in state "working"
  When I call lifecycle.move(lid, to_state="completed")
  Then an Event{name:"lifecycle_transition", to:"completed"} exists in the graph
  And it is OBSERVED_DURING the serving intent and the lifecycle

Scenario: a gate pause emits a durable transition event for free
  Given a Lifecycle serving the current intent
  When a gate fails (routing through lifecycle.move(→input-required))
  Then a lifecycle_transition Event to "input-required" exists (blocked = durable)
  And a MonitorEvent for the blocked transition is emitted

Scenario: a repeated identical transition does not spam graph events (panel A-2)
  Given a Lifecycle that moves failed→working→failed→working→failed
  Then the durable graph carries each distinct terminal transition once per occurrence
  But churn (working) stays on the monitor, never the graph

Scenario: transition events carry a sequence key for ordering (panel H-2)
  Given concurrent child transitions under one intent
  When manage.timeline orders them
  Then ordering is by the event's recorded_at (the bi-temporal vfrom), deterministic

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

**Partial — Slice 1 SHIPPED 2026-06-20 (intent f6aac283).** The emission core +
the B4 split land; the build-order note (after 340) is relaxed — 344 builds on the
shipped 339 `move` chokepoint, and 340's table guard layers in later without
touching the emit path.

Done:
- `agency/_lifecycle_events.py` — pure, engine-free `LifecycleEvent` dataclass
  (mirrors `LoopEvent`, Spec 156) + the B4 classifier (`is_durable_transition`,
  `DURABLE_STATES = terminal ∪ blocked`, derived from the `LifecycleState` enum —
  no hand-listed copy) + `TRANSITION_EVENT_NAME`.
- Emission folded into substrate `Lifecycle.move` (`_emit_transition`): **terminal/
  blocked** (`completed·failed·canceled·input-required·auth-required`) → durable
  graph `Event{name:"lifecycle_transition", from_state, to_state, lifecycle,
  evidence}` reusing the Spec 076 node, linked `OBSERVED_DURING` BOTH the serving
  Intent and the Lifecycle; **every** transition also fans a `MonitorEvent{source:
  "lifecycle", kind:"transition"}` onto the Spec 021 channel. Because emission
  lives in the SOLE writer, every routed writer emits for free.
- `engine.lifecycle` now built with `monitor=self.monitor` (monitor constructed
  first). `Lifecycle(memory)` without a monitor still records durable graph events
  (churn telemetry is the only monitor-gated part).
- **Gate pause routed through `move`** (advances 339b): `gate.check` +
  `lifecycle_gate`'s `input-required` write now call `ctx.lifecycle.move(…,
  "input-required")` (guarded against a no-op re-reject) — so a blocked transition
  is durable provenance, satisfying acceptance scenario 3.
- 6 acceptance scenarios in `tests/acceptance/features/lifecycle.feature` (churn→
  monitor-not-graph, terminal→durable+OBSERVED_DURING, blocked→durable, gate-pause-
  for-free, trail recoverable, appears in `manage.timeline`). Full lifecycle suite
  (15) green; gate/manage/jules/delegate/typed-fulfilment (128) green.

Storage note: `from`/`to` are graphqlite-Cypher reserved words (raw syntax error),
so the Event stores `from_state`/`to_state` (matching the dataclass fields) — the
spec sketch's `from:/to:` keys are renamed accordingly.

**Jules-review follow-up SHIPPED 2026-06-20 (the 349b lifecycle-source slice):**
the monitor emit was hardcoded as `self.monitor.emit` inside `move`. It now fans
onto the **Spec 349 pillar event bus** — `_emit_transition` calls
`_events.run(engine, "lifecycle:transition", ev)` and a registered subscriber
(`lifecycle.monitor`) emits the `MonitorEvent`. The durable graph `Event` record
stays inline (the lifecycle's intrinsic, engine-independent provenance); the
cross-cutting telemetry is the decoupled, subscribable part. This realises the
Spec 349 docstring's deferred "lifecycle events on the bus" — any capability can
now subscribe to `lifecycle:transition` (1 acceptance scenario proves fan-out).

Still (Slice 2): the `lifecycle.watch` consumer (Spec 341) reads this trail; the
dogfood loop-detector gains stall visibility over transition events; 340's table
guard runs before emit. The remaining unguarded writers (`subagent`, `music`) move
to `move` under 339b → they then emit for free too.
