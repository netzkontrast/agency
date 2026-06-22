---
spec_id: "341"
slug: lifecycle-observe-suite
status: partial
state: inprogress
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 4]
depends_on: ["022", "076", "290", "338", "339"]
domain: lifecycle
wave: program-master
parent_spec: "338"
---

# Spec 341 — The observe arm (`read · find · check · watch`) — REUSE, no new verbs

> Child of the Lifecycle-pillar deep program (Spec 338). The *observe* half of the
> CORE.md §3 frame.
>
> **Panel + pillar reframe (2026-06-20, panel F-1 + owner "it's a pillar").** The
> Lifecycle pillar owns the WRITE machine (`open/move/close` on the substrate);
> **observation is the Memory pillar's job, REUSED — this slice adds NO new
> `lifecycle.*` verbs.** `read`/`find` ARE `manage.state`/`manage.find` (Spec
> 290/330); `check` IS `gate.check` (which now routes its pause through
> `ctx.lifecycle.move(→input-required)`); `watch` IS `manage.timeline` over the 344
> events + the existing `jules.watch`. The slice's real work is the *wiring +
> contract*, not a verb surface. **N-2:** `watch` is a **pull** (it reads the
> recorded transition trail) — it is named for the frame, but live *push*
> notification remains `jules.watch`/the monitor channel; the spec says so plainly
> rather than implying a daemon.

## Why

CORE.md §3 names the observe frame `read · find · check · watch`. The reads
already exist — scattered: `manage.state`/`whats_next`/`timeline` (Spec 290),
`manage.open_intents` (Spec 290/330), the `jules` watcher (Spec 022), the Spec 076
event hook. What is missing is the **Lifecycle-centric frame** that an agent
reaches for to ask "what state is this lifecycle in, which lifecycles match a
filter, did this gate pass, and notify me when it transitions" — without knowing
which of four surfaces holds the answer. This slice is the thin, composing frame.

## Design (`clusters/observe.py` — all `role="act"`, read-only)

| Verb | Composes | Returns |
|---|---|---|
| `read(lifecycle_id)` | `manage.state` filtered to the one lifecycle + its serving Intent + `PERFORMED_BY` Agent | `{lifecycle_id, state, phase, kind, intent_id, agent_id, gates}` |
| `find(state="", intent_id="", agent_id="")` | graph `find("Lifecycle")` + `_live` filter (mirrors `manage._live`) | `{count, lifecycles: [...]}` (filtered, live-only) |
| `check(lifecycle_id, name, passed, evidence="")` | the `gate.check` predicate + a `lifecycle.move(→input-required)` on failure | `{passed, gate, state}` |
| `watch(lifecycle_id="", scope="intent")` | the **Spec 344 `lifecycle_transition` Event trail** (primary) + the `jules.watch` poller (jules dispatches) + the `MonitorEvent` SLOG (Spec 021) | `{watching, transitions: [...], events: [...]}` |

**Reuse contract (the anti-dormant rule).** Each verb is a *projection* over an
existing surface:

- `read` MUST call `manage.state` (or its `IntentStore` join) — it does not
  re-query the graph for what `manage` already assembles. It narrows to one
  lifecycle and adds the gate roll-up.
- `find` reuses the `_live` (bi-temporal latest-wins) helper from `manage`, not a
  second implementation.
- `check` reuses the `gate.check` predicate path and the `lifecycle.move` guard
  (339/340) — a failed check is a *transition* (`→input-required`), closing the
  CORE.md "Gates = input-required → Intent re-entry" loop. `check` is the frame
  alias; `gate.check`/`gate.adjudicate` stay for reusable predicates.
- `watch` does NOT poll in a busy loop — for ANY lifecycle it reads the
  **Spec 344 `lifecycle_transition` Event trail** (`OBSERVED_DURING` the lifecycle),
  which is the recorded transition history `move` emits. For a jules dispatch it
  ALSO surfaces the existing `jules.watch` poller (Spec 022) and the `MonitorEvent`
  SLOG (Spec 021). 344 is what makes `watch` event-driven rather than a re-scan;
  without it `watch` would have to poll `state` (the gap 344 closes). (No new
  polling daemon — YAGNI; CLAUDE.md #76 capture stays full.)

### The management board Document (`templates/lifecycle-board.md`)

`read`/`find` populate the Spec 292 convergence Document — a renderable board of
in-flight lifecycles, their states, and what blocks each (reusing
`manage.render`'s dashboard, scoped to lifecycles). This is how the observe suite
surfaces as a *file* peer, not only a wire payload.

### What this slice does NOT do

- No new read storage — every verb reads the existing graph/`manage`/`jules`
  surfaces.
- No new event source — `watch` composes the Spec 076 hook; it does not add a
  hook.

## Acceptance (Gherkin)

```gherkin
Scenario: read projects manage.state to one lifecycle
  Given an open Lifecycle in state "working" serving an intent
  When I call lifecycle.read(lid)
  Then it returns state, serving intent_id, agent_id, and the gate roll-up
  And it does so via manage.state (not a hand-written graph query)

Scenario: find filters live lifecycles by state
  Given two lifecycles, one "working" and one "completed"
  When I call lifecycle.find(state="working")
  Then only the working lifecycle is returned (live-only)

Scenario: check failure is a transition, not an update
  Given an open Lifecycle in state "working"
  When I call lifecycle.check(lid, name="spec-review", passed=False)
  Then the Lifecycle reaches "input-required" via lifecycle.move
  And a BLOCKED_ON gate edge is recorded

Scenario: watch returns the transition trail without polling
  Given a Lifecycle that has moved submitted→working→input-required
  When I call lifecycle.watch(lid)
  Then it returns the ordered transition trail and any OBSERVED_DURING events
```

## Followup — Implementation Status (2026-06-20)

**Slice 1 SHIPPED 2026-06-20** — the observe frame, REUSED on the Memory pillar
(`manage`), resolving the spec's reframe-vs-design tension: the frame lands as
`manage` verbs (observation is the Memory pillar's job), NOT new `lifecycle.*`
verbs (Lifecycle is the WRITE substrate). The mapping:

- **`find` = `manage.list("Lifecycle", where={state})`** — pure reuse (the
  existing generic list + `_live`); NO new verb.
- **`check` = `gate.check`** — pure reuse; a failed check already routes its pause
  through `ctx.lifecycle.move(→input-required)` (Spec 339/344); NO new verb.
- **`read` = NEW `manage.lifecycle(lifecycle_id)`** — a one-call rollup
  (state · phase · kind · parameterization · serving intent · agent · gates),
  composing `recall_typed` + the SERVES/DISPATCHED_TO/PASSED/BLOCKED_ON edges. No
  new storage.
- **`watch` = NEW `manage.lifecycle_trail(lifecycle_id)`** — the ordered Spec 344
  `lifecycle_transition` Event trail `OBSERVED_DURING` the lifecycle (a PULL over
  the durable history; only terminal/blocked transitions are durable per the 344
  B4 split). Live PUSH stays `jules.watch` (Spec 022) + the Spec 021 monitor.

4 acceptance scenarios (`tests/acceptance/features/lifecycle_observe.feature`);
the reuse contract held (no duplication of `manage`'s `_live`/`list`). manage +
gate + lifecycle suites green; install regen + the lifecycle reference doc
updated. **Still (Slice 2):** the `lifecycle-board.md` convergence Document
(render the in-flight board via `manage.render`); folding `jules.watch` into a
unified `manage.lifecycle_trail(scope="jules")` view.
