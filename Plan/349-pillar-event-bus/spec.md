---
spec_id: "349"
slug: pillar-event-bus
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 3]
depends_on: ["021", "076", "156", "195", "290", "334", "344"]
domain: events
wave: program-master
parent_spec: "076"
---

# Spec 349 — The pillar event-registration bus (subscribe · emit · configure)

> Owner directive: *"extend the lifecycle events to have all events (also hooks)
> configurable (config.yaml) for external hooks, and a way for capabilities,
> intent and Memory to register themselves for events — so a capability can emit
> a snippet when, for instance, the develop capability receives a pre-tool hook
> and sees this is the first time this tool is used; then it emits relevant
> information to the agent, but only once. And then many more events each
> capability — or each pillar — can emit."* This spec designs that bus.
>
> **Scope (owner Q4 = "full architecture, no build"):** this is a complete
> design record — taxonomy, registration model, config surface, the reference
> subscriber, the failure/ordering contract. It picks **no** implementation
> target. The Gherkin below is the contract a later slice spec implements.

## Why

Agency already has the *primitive* and three disconnected *event sources*; what it
lacks is the *bus* that lets any pillar declare interest and react.

**The open primitive (verified, `agency-infra.md` §2):** hook handlers live in a
per-engine dict `engine._hook_handlers` (engine.py:704-708) with a public
`register_hook_handler(event_name, fn)` (engine.py:764-768); `dispatch_hook`
routes exact-match-else-`*`-catch-all (engine.py:770-779). It is an **open set**,
not an if/elif. **But the dict is seeded once in `Engine.__init__` and no loop
reads capability-declared subscriptions.** Capabilities self-register *verbs* (by
reflection) — they cannot self-register *event interest*. That missing loop is the
heart of this spec.

**The three event sources today, unconnected:**

- **Hook events** (Spec 076) — `dispatch_hook` records one `Event` per Claude Code
  lifecycle hook (`SessionStart`, `PreToolUse`, `PostToolUse`, `UserPromptSubmit`,
  `Stop`, …), `OBSERVED_DURING` the active intent.
- **Lifecycle transition events** (Spec 344, draft) — every `lifecycle.move` will
  emit a typed `LifecycleEvent` (terminal/blocked → graph `Event`; churn →
  monitor).
- **Capability-internal effects** — e.g. `frugal.debt` harvesting markers, a gate
  passing — emit *nothing* a third party can react to.

**The reference need (the owner's concrete example):** the `frugal` capability
(Spec 348) wants to react to `PreToolUse` and, the **first** time a given tool is
used in a session, inject a relevant snippet — then stay silent. Spec 195 Slice 2
(SHIPPED) already injects MCP-equivalent suggestions on raw-tool use via
`_pre_tool_use_handler` → `hookSpecificOutput.additionalContext`, but it (a) fires
*every* time, and (b) is hardcoded in the engine, not a capability subscription.
The bus generalizes it: **a capability declares the subscription; the bus dedups
once-per-session; the engine stays generic.**

Goal 3 (agent-uniform lifecycle, no special-casing) and Goal 2 (the provenance
moat) both want reactions to be *declared and recorded*, not hand-wired in the
engine per case.

## Design

### 1. A unified event taxonomy

One namespace covers every source, so a subscriber registers for any of them with
the same shape: **`<source>:<name>[:<qualifier>]`**.

| Source | Examples | Backed by |
|---|---|---|
| `hook:` | `hook:PreToolUse`, `hook:SessionStart`, `hook:Stop` | Spec 076 dispatch |
| `lifecycle:` | `lifecycle:transition:completed`, `lifecycle:transition:blocked` | Spec 344 `LifecycleEvent` |
| `capability:` | `capability:frugal:debt_harvested`, `capability:gate:passed` | `event.emit` (§5) |
| `*` | every event (the existing catch-all) | Spec 076 |

The taxonomy is a *string convention*, not a new enum to maintain (CLAUDE.md #8 —
open set). `dispatch_hook` already matches `event_name` then `*`; the bus extends
the same matcher to the `<source>:` prefixes.

### 2. Declarative subscriptions (the missing loop)

A pillar declares interest the same way it declares verbs/skills — as data on its
registration, not an imperative `register_hook_handler` call:

```python
# on a capability's ontology / registration
subscriptions = [
    Subscription(
        event="hook:PreToolUse",
        handler="on_first_tool_use",   # a method on the capability
        once_per="session.tool",       # dedup key (§6); "" = every time
        filter={"tool_name": "*"},     # optional predicate
        priority=50,                   # lower runs first (§7)
    ),
]
```

At engine bootstrap, **one loop** walks every discovered capability (and the
intent/memory pillars, §3), reads `subscriptions`, and calls the existing
`register_hook_handler(event, bound_handler)` — closing the gap the infra audit
found. The primitive is unchanged; the bus is the *reader* that was missing.

> **Why declarative, not imperative:** a declared subscription is inspectable
> (`search`/`manage` can list "who listens to `hook:Stop`"), driftable
> (`# AGENCY-DRIFT: event-subscribers`), and recorded — an imperative
> `register_hook_handler` in `__init__` is none of these. Same reasoning as
> verbs-by-reflection.

### 3. The three pillars are symmetric subscribers

Not only capabilities — **Capability · Intent/Lifecycle · Memory** all register
interest, treated uniformly (the "each pillar can emit" directive):

- **Capability** — `frugal` subscribes to `hook:PreToolUse` (the reference, §4);
  `gate` could subscribe to `lifecycle:transition:blocked`.
- **Intent / Lifecycle** — subscribes to `lifecycle:transition:blocked` to record
  a blocker on the serving intent; to `hook:UserPromptSubmit` for the Spec 321
  new-intent watch (already hook-driven — folds onto the bus).
- **Memory** — subscribes to `hook:Stop` / `hook:SessionEnd` to persist a
  reflection; to `capability:*:*` to accrue cross-session observations.

Each subscriber is a small handler returning either `additionalContext` (text to
inject back to the agent) or a side effect (a graph write). Symmetry means a new
pillar reaction is a *subscription*, never an engine edit.

### 4. The reference subscriber — first-use-once emit

The owner's concrete example, fully specified (this is the bus's canonical proof):

```
event:     hook:PreToolUse
subscriber: frugal (Spec 348)
handler:   on_first_tool_use(event) ->
             tool = event["tool_name"]
             if already_emitted(session_id, tool):  return {}      # silent
             snippet = frugal.instructions(compact=True, for_tool=tool)
             mark_emitted(session_id, tool)                          # once
             return {"additionalContext": snippet}
once_per:  "session.tool"     # dedup key = (session_id, tool_name)
```

- **Generalizes Spec 195 S2:** S2 emits MCP suggestions *every* PreToolUse; the
  bus adds the *once-per-(session,tool)* dedup and moves the trigger from a
  hardcoded engine handler to a `frugal` subscription. S2's
  `additionalContext` channel is reused verbatim.
- **The "once" state is in the graph,** not a process global: each emit records an
  `Event{name:"first_use_emit", session, tool, subscriber}` (Spec 076 node,
  full-capture). `already_emitted` is a graph read of that event for
  `(session, tool)` — so dedup survives within the session and is *queryable*
  (replayable via `dogfood.replay_events`, Spec 195).
- **Many more emits follow the same template:** `gate` on first failure, `develop`
  on first edit of an unfamiliar file, `research` on first web fetch — each a
  subscription, each once-keyed, each recorded.

### 5. The emission API — `event.emit`

A capability emits a custom event (the third source) with one verb:

```
event.emit(name="capability:frugal:debt_harvested", payload={...})
  -> records Event{name, payload} OBSERVED_DURING the active intent
  -> fans out to every subscriber of that event (and of "*")
```

Spec 344's `LifecycleEvent` becomes the *lifecycle-shaped special case* of
`event.emit` (it already records an `Event`; the bus just adds the fan-out step).
No new node type — every emission is a Spec 076 `Event` (reuse, per Spec 344's own
"reuse, not a new event system"). The `event` substrate (a tiny capability or a
`ctx.events` substrate surface — slice spec decides) owns `emit` + the registry
read verbs (`event.subscribers(event)`, `event.log(intent)`).

### 6. config.yaml — external hooks + subscription overrides (deferred impl)

A `config.yaml` `events:` section lets a user wire reactions **without code** —
external hooks (shell/webhook) and subscription toggles:

```yaml
events:
  subscriptions:
    - event: "lifecycle:transition:completed"
      run: "./scripts/notify.sh"        # external hook — LATER to implement
    - event: "hook:PreToolUse"
      emit: "frugal:first_use_snippet"
      once_per: "session.tool"
    - event: "capability:gate:blocked"
      disable: true                      # opt out of a built-in subscription
```

**Constraint the infra audit surfaced (`agency-infra.md` §4):** `_config.py` is an
open registry but **no list-valued config round-trips through the scaffold today**
— only scalars. The `events.subscriptions` list needs a **list-aware
`_yaml_scalar` branch** (a documented `_config` extension this spec calls for).
The *external-hook runner* (executing `run:` targets) is explicitly **later to
implement** — this spec defines the config shape and the safety contract
(external hooks run sandboxed, time-bounded, failure-isolated like the Node
graceful-degrade contract), not the runner.

### 7. Ordering, dedup, and failure-isolation (the safety contract)

- **Ordering.** Multiple subscribers on one event run in ascending `priority`,
  then registration order — deterministic.
- **Dedup.** `once_per` keys (`"session"`, `"session.tool"`, `"intent"`, `""`) are
  resolved against recorded emit-Events (§4), not memory — survives compaction
  within a session.
- **Failure-isolation.** A subscriber that raises is logged and skipped; it
  **never** breaks the triggering hook/transition (the `frugal_prefix` "never
  raises" precedent, `_frugal.py:120-128`). One bad subscriber can't take down
  `PreToolUse`.
- **No new async.** Claude Code hooks are synchronous; the bus dispatch stays
  synchronous within the hook call. External hooks (§6) are the only path that may
  fan out to a subprocess, and they are time-bounded.
- **Provenance.** Every delivery records the Event `OBSERVED_DURING` the intent
  with a `DELIVERED_TO`/`EMITTED_BY` edge to the subscriber/emitter — so "what
  reacted to what" is a graph query, replayable.

### 8. Flow

```
trigger:  hook stdin  |  lifecycle.move  |  capability event.emit
   |             |              |
   +------> normalize to <source>:<name>[:<qualifier>] ------+
                                                             v
                          resolve subscribers (declared §2/§3 + config §6)
                                                             v
                     for each, ascending priority:
                        filter? + once_per dedup (graph §6) ──skip──> next
                        run handler  ── raises ──> log + skip (§7)
                        record Event OBSERVED_DURING intent + DELIVERED_TO edge
                        collect additionalContext
                                                             v
                     external subscriptions (config §6) → sandboxed run (LATER)
                                                             v
                     aggregate additionalContext → return to host
```

### What this spec does NOT do (no build)

- No implementation — design record only (owner Q4). A later slice spec
  (`349a …`) implements the bootstrap loop + `event.emit` + the first-use-once
  subscriber.
- No new `Event` node type — reuses Spec 076 (per Spec 344).
- No external-hook *runner* — §6 defines the config shape + safety contract; the
  runner is "later to implement".
- No async/daemon — synchronous within the hook (§7).
- No change to Spec 332 frugal content or Spec 348's verb surface — `frugal` is a
  *consumer* of this bus, designed in 348, subscribing per §4.

## Acceptance (Gherkin — the contract a later slice implements)

```gherkin
Scenario: a capability declares a subscription and the bus registers it
  Given a capability declaring subscriptions=[{event:"hook:PreToolUse", handler:"on_first_tool_use"}]
  When the engine boots
  Then register_hook_handler was called for "hook:PreToolUse" with that handler
  And manage/search can list it as a subscriber of that event

Scenario: first use of a tool emits once, then stays silent
  Given the frugal first-use subscription is active in a session
  When PreToolUse fires for tool "Bash" the first time
  Then additionalContext carries the frugal snippet
  And an Event{name:"first_use_emit", tool:"Bash"} is recorded
  When PreToolUse fires for tool "Bash" again in the same session
  Then no snippet is emitted (once_per session.tool)

Scenario: one capability emits, another reacts
  Given memory subscribes to "capability:frugal:debt_harvested"
  When frugal.debt calls event.emit("capability:frugal:debt_harvested", payload)
  Then memory's handler runs and the delivery is recorded DELIVERED_TO memory

Scenario: intent and memory are symmetric subscribers
  Given intent subscribes to "lifecycle:transition:blocked"
  When a lifecycle moves to "input-required"
  Then the intent handler records a blocker on the serving intent

Scenario: a failing subscriber never breaks the trigger
  Given a subscriber whose handler raises
  When its event fires
  Then the triggering hook still returns normally
  And the failure is logged, the other subscribers still run

Scenario: config.yaml registers an external hook (shape only; runner deferred)
  Given events.subscriptions in .agency/config.yaml with a run: target
  When config loads
  Then the list-valued subscription round-trips through _config
  And the external-hook target is recorded as a pending subscription (not yet executed)

Scenario: every delivery is replayable provenance
  Given several emits during an intent
  When I call dogfood.replay_events(intent_id)
  Then each delivery appears as an Event in recorded order
```

## Followup — Implementation Status (2026-06-20)

Not started — **design record, no build** (owner Q4). Opened by the owner's
"events configurable + pillars register for events + first-use-once emit"
directive. Designs the bus on top of the *open* `register_hook_handler` primitive
(Spec 076, shipped) that no loop currently reads: a `<source>:<name>` taxonomy,
declarative `subscriptions` on capability/intent/memory read by one bootstrap
loop, an `event.emit` fan-out reusing the Spec 076 `Event` node, a `config.yaml`
`events:` registry (needs the list-valued `_config` branch; external-hook runner
deferred), and the first-use-once reference subscriber that generalizes the
shipped Spec 195 Slice 2. Safety contract: deterministic priority, graph-keyed
`once_per` dedup, failure-isolation (the `frugal_prefix` precedent), synchronous
dispatch. `frugal` (Spec 348) is the reference emitter/subscriber. **Improves**
Spec 344 (its `LifecycleEvent` becomes the lifecycle-shaped `event.emit`) and Spec
347 (the frugal stamp/first-use emit are delivered via this bus) — cross-refs
added to both. A later `349a` slice implements the bootstrap loop +
`event.emit` + the first-use-once subscriber.
