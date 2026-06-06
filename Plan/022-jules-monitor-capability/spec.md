---
spec_id: "022"
slug: jules-monitor-capability
status: done   # Shipped 2026-06-06 (branch claude/affectionate-meitner-H4vTJ)
owner: "@agency"
depends_on: ["012", "013", "021"]   # 012 = watcher; 013 = INSTRUCTIONS; 021 = channel
affects:
  - agency/capabilities/_jules_watch.py   # emit through ctx.engine.monitor on transitions
  - agency/capabilities/jules.py          # emit on dispatch/recover/verify
  - tests/test_jules_monitor.py           # new — coverage of emitted events
estimated_jules_sessions: 0
domain: capability
wave: 3
---

# Spec 022 — Jules events surface through the engine monitor (first real use of Spec 021)

## Why

Spec 021 lands the engine-level monitor channel — one `monitors/monitors.json`
entry, many capability event sources fanning in. This spec is the FIRST
real use: the Jules watcher's state transitions become live notifications
in Claude Code.

The orchestration problem this closes: today, when the orchestrator
dispatches Jules + walks away, **the watcher's `WatchEvent`s land in a
per-intent asyncio Queue inside the engine process**. If the orchestrator
isn't actively calling `jules.watch(...)`, the events accumulate
unseen. From a Claude Code session (where the user is doing other
things between dispatches), live awareness costs a polling loop the
orchestrator has to remember to run.

**The monitor channel fixes this without exposing a separate Jules-only
monitor** (which would violate "every improvement here is carried
through the complete system" — the user's directive). The Jules watcher
adds ONE call to `ctx.engine.monitor.emit(MonitorEvent(...))` per
classified transition; the agent reads the same stream that future
capabilities also feed.

## Done When

- [ ] **`_jules_watch.Watcher._poll_loop` emits a `MonitorEvent` on every
  classified transition** (alongside the existing per-intent queue put).
  The classifier `_classify(...)` already produces a structured event
  shape; the emit translates it. Event fields:
  ```python
  MonitorEvent(
      source="jules",
      kind=event["action"],             # one of the 9 WatchActions
      message=f"sid={sid} {prev_state}→{state}: {event['instruction'][:200]}",
      intent_id=sinfo["intent_id"],
      ts=time.time(),
  )
  ```

- [ ] **No duplicate queue + monitor.** The per-intent queue stays
  (programmatic consumers like `jules.watch` need it); the monitor is
  the SIDE-CHANNEL for live awareness. Both fire on the same transition;
  test asserts both land.

- [ ] **`jules.dispatch` emits on session creation**:
  ```python
  ctx.emit_monitor(source="jules", kind="dispatched",
                   message=f"sid={sid} state=QUEUED title={title}",
                   intent_id=ctx.intent_id)
  ```
  So the user sees "dispatched" immediately in CC, not just when the
  first state transition fires (seconds-to-minutes later).

- [ ] **`jules.recover` emits on session promotion to recovery_in_flight**:
  ```python
  ctx.emit_monitor(source="jules", kind="recovery_started",
                   message=f"sid={sid} entering recovery (probe budget: 3 × 5min)",
                   intent_id=ctx.intent_id)
  ```

- [ ] **`jules.verify` emits on the `branch_on_remote=False` path**:
  silent-fail detection becomes visible without the user reading the
  `verify` return value.

- [ ] **NO new `monitors/monitors.json` entry.** Spec 022 must not modify
  the install's monitors file at all — all events flow through Spec 021's
  single `agency-engine` entry. Regression test: `python -m agency.install`
  produces a `monitors/monitors.json` with `len(entries) == 1` after
  Spec 022 lands.

- [ ] **Tests** (`tests/test_jules_monitor.py`):
  - Watcher transition (mocked clock + stubbed API) → MonitorEvent
    appended to the engine's monitor.log AND the per-intent queue.
  - `jules.dispatch` → MonitorEvent with `kind="dispatched"`.
  - `jules.recover` → MonitorEvent with `kind="recovery_started"`.
  - `jules.verify` with `branch_on_remote=False` → MonitorEvent with
    `kind="silent_fail_detected"`.
  - `monitors.json` contains exactly one entry post-install.

- [ ] **AGENCY_PROTOCOL.md doc update** — add a short section explaining
  that Jules state transitions surface via the engine monitor stream;
  orchestrators reading CC's notification feed know Jules state changes
  WITHOUT polling.

## Files

- **Modify:**
  - `agency/capabilities/_jules_watch.py` — `_poll_loop` calls
    `engine.monitor.emit(...)` per transition (~5 LOC + the event
    construction).
  - `agency/capabilities/jules.py` — `dispatch`, `recover`, `verify`
    each gain a `ctx.emit_monitor(...)` call (~3 lines per verb).
  - `AGENCY_PROTOCOL.md` — new section: "Live awareness via the
    engine monitor stream."

- **Create:**
  - `tests/test_jules_monitor.py` — coverage of the contract above.

## Open Questions

1. **Token cost of monitor events flowing to the agent.** Every transition
   = one stdout line ≈ ~80 chars typically. A noisy session (many
   state transitions) could spam the agent's notification feed.
   Recommend: emit only on **state-change** transitions
   (the existing `_classify` already deduplicates same-state); the `noop`
   action does NOT emit (Spec 022 v1 filter at the emit call site).

2. **Should `recover_silent_fail` emit a HIGH-PRIORITY event?** Today CC's
   notification API is uniform (one line = one notification). Future
   work could prefix events with `[ALERT]` or `[INFO]` for the agent
   to filter on. Recommend NO priority field in v1; defer until CC's
   monitor API gains priority levels OR we observe noise-vs-signal
   problems in practice.

3. **Cross-session continuity.** Spec 021 OQ5 already raises this; the
   answer applies: events emitted while CC was disconnected are visible
   in the log file but NOT delivered as live notifications. For Jules
   that's fine — the GRAPH carries `JulesSession` + `JulesWatchEvent`
   nodes (Spec 012 ontology), so on next session the orchestrator can
   query `memory.provenance(intent_id)` and find every transition
   that fired.

4. **Should `delegate.fan_out` ALSO emit completion events?** That's
   Spec 023 territory (the second user of Spec 021). Not in 022.

## Evidence

- `agency/capabilities/_jules_watch.py` (the watcher this spec hooks).
- `Plan/012-jules-complete-lifecycle-and-watcher/spec.md` (the watcher
  + per-intent queue this spec extends with the side-channel emit).
- `Plan/013-jules-skills-and-capability-improvements/DESIGN.md` (the
  INSTRUCTIONS template strings this spec reuses for the
  monitor.message body).
- `Plan/021-engine-monitor-channel/spec.md` (the substrate).
- User's directive ("we don't want to expose too many Monitors") — the
  hard constraint this spec respects by routing all Jules events
  through Spec 021's single engine channel.

## Followup — Implementation Status (2026-05-31)

> Consolidation pass on branch `claude/plan-spec-review-74gHM`. Frontmatter `status:` may be stale; this section reflects verified code state.

**Verdict:** Not started

### Done
- Nothing. No code for Spec 022 exists yet.

### Still to implement
- **Spec 021 (dependency) has not shipped.** `agency/_monitor.py` does not exist; `monitors/monitors.json` directory does not exist; `CapabilityContext.emit_monitor()` is not present in `agency/capability.py`; `Engine.monitor` is not wired in `agency/engine.py`. All of Spec 021's substrate is missing — Spec 022 is fully blocked.
- Once 021 ships: `_jules_watch.Watcher._poll_loop` needs `MonitorEvent` emit per classified transition; `jules.dispatch`, `jules.recover`, `jules.verify` each need a `ctx.emit_monitor(...)` call; `tests/test_jules_monitor.py` needs to be created; `AGENCY_PROTOCOL.md` needs the monitor-stream section.

### Refinement needed (given later specs)
- None beyond the 021 dependency. Spec 022's design is well-scoped and self-consistent. Once 021 lands, implementation is straightforward (~5 LOC per emit site + one new test file).

### Evidence
- code: absent — no `agency/_monitor.py`, no `monitors/` directory, no `ctx.emit_monitor` in `agency/capability.py` or any capability
- tests: none (`tests/test_jules_monitor.py` not found; `tests/test_engine_monitor.py` not found)
- commits/notes: Plan/000-overview.md lists 022 as "In flight (drafted; awaiting design loop)" behind Spec 021; `status: draft` in frontmatter is accurate but understates the blocking: the dependency is entirely unimplemented.

## Followup — Implementation Status (2026-06-06)

> Shipped on branch `claude/affectionate-meitner-H4vTJ`, immediately after its
> dependency Spec 021 landed on the same branch/PR (#20).

**Verdict:** Shipped

### Done
- `agency/capabilities/jules/watch.py` — `Watcher._emit_monitor(sinfo, event)`
  fans each classified transition onto `engine.monitor` (Spec 021); called from
  `_poll_loop` right after `_put_event` (queue + monitor both fire on the same
  transition). `noop` actions are filtered (OQ#1); silent no-op when no
  engine/monitor attached. Message = `sid={sid} {prev_state}→{state}: {instr[:200]}`,
  `kind` = the WatchAction.
- `agency/capabilities/jules/_main.py` — verb-level emits via `ctx.emit_monitor`:
  `dispatch` → `dispatched` (on session create, inside the `if sid:` graph block);
  `recover` → `recovery_started`; `verify` → `silent_fail_detected` on the
  `branch_on_remote=False` path (COMPLETED≠done made visible without reading the
  return value).
- `AGENCY_PROTOCOL.md` §10 "Live awareness via the engine monitor stream" — the
  four emit points + the side-channel/durable-graph distinction + the
  single-monitor constraint.

### Tests
- `tests/test_jules_monitor.py` — 7 tests: watcher transition emits + keeps the
  queue; noop filtered; emit no-op without engine; `dispatch`/`recover`/`verify`
  emit their kinds with the serving intent_id; and the hard constraint —
  `install.generate()` still yields exactly ONE `agency-engine` monitors.json
  entry. All green; full suite 705 passed / 3 skipped.

### Open questions — resolved as specced
- OQ#1 (token cost): emit only on non-`noop` transitions. OQ#2 (priority field):
  none in v1. OQ#3 (cross-session): graph carries durable `WatchEvent` history;
  monitor is live-only. OQ#4 (`delegate.fan_out` events): out of scope — Spec 023.
