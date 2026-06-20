# Spec 349 — Spec-panel review (critique mode)

> Panel: Hohpe (integration/messaging — lead), Nygard (failure/ops), Fowler
> (boundaries/home), Newman (evolution), Wiegers (testability), Adzic (examples).
> Mode: critique. Score **6.8/10** → **8.1/10** after the folds. 2 blockers, 4
> majors, 2 minors. A "no-build" spec still owns a sound *contract*, so the panel
> reviewed the architecture as if it must survive implementation.

## Blockers

**B1 — Fowler (citing the Spec 338 precedent): decide the home — the bus is
SUBSTRATE, not a capability.** §5 hedges: "a tiny capability or a `ctx.events`
substrate surface — slice spec decides." That fork is exactly the one Spec 338
already resolved for lifecycle ("lifecycle isn't a capability — it's its own
pillar"). The event bus is the same shape: a cross-cutting substrate every pillar
depends on, seeded in `Engine.__init__`, owning no domain. A `capability_events_*`
verb that the engine must call during hook dispatch would be a layering inversion
(the substrate calling a capability). → **FOLD:** resolve to **substrate** —
`ctx.events` + `event_*` substrate tools (like `hook_event`, `lifecycle_*`),
**not** `agency/capabilities/events/`. `emit`/`subscribers`/`log` are substrate
tools; capabilities *consume* them. Mirror the 338 reframe explicitly.

**B2 — Nygard + Hohpe: re-entrancy is unbounded.** A subscriber may call
`event.emit` (§5), whose fan-out may hit a subscriber that emits again. Nothing
caps this. On a synchronous in-hook dispatch (§7) that is a stack-overflow / hang
on the hot path, and a `PreToolUse` storm if a tool-use emit triggers a tool-use.
→ **FOLD:** add the re-entrancy contract — emits raised *inside* a delivery are
**enqueued and drained after** the current fan-out (breadth-first), with a hard
depth/þfan cap (config, default e.g. 3 / 64) beyond which further emits are
dropped-with-warning (the keep-full warn-don't-cut precedent applies to the log,
not the dispatch). Synchronous dispatch stays; re-entrant emits do not recurse.

## Majors

**M1 — Hohpe: the `additionalContext` aggregation semantics are undefined.**
Multiple subscribers on one `hook:PreToolUse` each may return injection text (§8
says "aggregate" — how?). Order? Dedup? Size bound? Unspecified, two subscribers
could flood the agent's context or contradict each other. → **FOLD:** define the
merge — ordered by subscriber `priority` then name, deduped by content hash,
**token-bounded** (reuse `shell.filter`, which the search flagged "hook-ready"),
each fragment labelled with its emitter. A collecting channel needs a budget.

**M2 — Nygard: graph-keyed `once_per` on the `PreToolUse` hot path is too
expensive.** §6 resolves dedup "against recorded emit-Events … not memory."
`PreToolUse` fires on *every* tool call; a graph query per call to check
`(session,tool)` will dominate latency. → **FOLD:** dedup is an **in-session memo
written through to the graph** — the memo (a `set` keyed by `session.tool`) is the
read path (O(1)); the `first_use_emit` Event is the durable record written once on
first emit. Graph is the source of truth on a cold session; the memo is the hot
path. (The Event still makes it replayable — §4 unchanged.)

**M3 — Wiegers + repo rule 7: the acceptance tests assert implementation, not
behaviour.** "register_hook_handler was called for …" tests an internal call —
exactly what CLAUDE.md rule 7 ("test behaviour, not implementation") forbids. →
**FOLD:** re-altitude every scenario to observable behaviour: *"when the event
fires, the subscriber's handler runs and its effect is observable"* — never *"the
registration function was called."* The bootstrap-loop scenario becomes: a
declared subscription, when its event fires, produces the subscriber's effect.

**M4 — Newman: payload evolution is unaddressed.** `capability:` custom events
carry free-form payloads; a subscriber in another pillar breaks silently if an
emitter renames a field. → **FOLD:** payloads are **emitter-typed and
append-only** — fields are added, never renamed/removed within a name; subscribers
MUST tolerate unknown fields (forward-compat). One sentence + a scenario where an
extra field doesn't break a subscriber.

## Minors

**m1 — Adzic: `config disable:` needs a subscription identity.** "Opt out of a
built-in subscription" — keyed how? → **FOLD:** by `(event, handler)` pair; a
`disable` with no matching declared subscription is a config warning, not a
silent no-op.

**m2 — Cockburn: name the trust boundary for external `run:` hooks.** A
config-declared shell hook runs with the user's privileges — the repo owner
editing `config.yaml` IS the trust boundary (same shape as ponytail trusting
`node` on PATH). → **FOLD:** state it; the deferred runner inherits the
sandbox/time-bound contract from §6, and external hooks never run from anything
but the project's own `config.yaml`.

## Consensus

Hohpe: "the unification of hook + lifecycle + capability events under one
subscribe API is the right call — defend it, don't hedge it." The two blockers are
structural: **B1** (substrate, not capability — the 338 precedent decides it) and
**B2** (re-entrancy — an event bus without a re-entrancy contract is a hang
waiting to happen). The four majors harden the hot path (M2), the collecting
channel (M1), the test altitude (M3), and forward-compat (M4). None require a
build — they tighten the contract a `349a` slice will implement. Post-fold the
architecture is implementable as written.

## 2nd pass — post-fold verification (2026-06-20)

Blockers B1 + B2 verified resolved. **Score 8.1 → 8.5, no open blockers.** Two new
folds, both from the agency hook PROCESS model:

**M5 — Nygard/process model: the M2 "in-session memo" cannot be a process
global.** Spec 076 runs each hook via the `agency hook` CLI — a FRESH PROCESS per
event. An in-process memo dies between `PreToolUse` calls, so dedup would never
fire. → FOLD: the `once_per` memo is the **Spec 336 ephemeral
`.agency/toolcalls.db`** (already session-scoped, already in the hook path) —
first-use is an indexed lookup + write-through there (O(1), survives across the
per-event processes); the durable `first_use_emit` Event still backs replay. This
makes M2 concrete AND reuses shipped infra (the ladder: installed dependency over
new code).

**M6 — the synchronous drain completes before the hook returns.** B2's
enqueue-drain runs after the current fan-out but MUST finish within the same hook
invocation — the host consumes `additionalContext` from the return; a drain
deferred past return is invisible. → FOLD (clarify): "drained breadth-first after
the current fan-out" = still within the one synchronous hook call, just not
recursive; nothing crosses the return boundary.
