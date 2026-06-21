---
spec_id: "342"
slug: agent-as-lifecycle-parameterization
status: shipped
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 4, 9]
depends_on: ["012", "040", "338", "339", "340"]
domain: lifecycle
wave: program-master
parent_spec: "338"
---

# Spec 342 — Agent as a Lifecycle parameterization (the unifying model)

> Child of the Lifecycle-pillar deep program (Spec 338). Realizes the CORE's most
> distinctive Lifecycle idea: **"an agent IS a Lifecycle parameterization"** — an
> agent-session is a lifecycle whose transitions/observers differ. This is the
> slice that turns the 10 `home="lifecycle"` capabilities from orphan
> "parameterizations of nothing" into variant configurations of **one managed
> machine**.

## Why

This slice realizes **Goal 3 head-on**: *"Agent-uniform lifecycle. An agent IS a
Lifecycle parameterization — Jules, Claude Code, future LLMs — sharing one
hard-gate pattern, one `SERVES` edge, one recovery flow. The aim is no
special-casing per agent."* CORE.md §3 says the same: *"a remote async agent
inserts `verify`; `COMPLETED ≠ done`."*

**The codegraph deep-analysis found this idea is already half-built — and
broken-in-half.** The two halves exist but are not connected:

- `delegate.fan_out` (`delegate/_main.py:489`) literally comments **"an agent IS a
  Lifecycle parameterization"** as it links `DISPATCHED_TO` — but the
  parameterization is only an edge + an `Agent{runtime}` node, with no variant
  transitions. `delegate.join` (`:521`) then computes `done` from the **raw** child
  `state == "completed"`.
- `jules.verify` (`jules/_main.py:332`) **already** enforces `COMPLETED ≠ done` —
  it independently re-checks the branch landed on origin via `vcs.remote_exists`
  (`_vcs.py:60`) and emits a `silent_fail_detected` monitor event — **but it
  returns a `{done}` dict and never writes the lifecycle**, and nothing in the
  `fan_out`/`join` path calls it.

So the substrate has **two contradictory "done"s** for one dispatch (N3): a local
subagent is "done" at raw `completed`, while a Jules run needs the remote check —
exactly the per-agent special-casing Goal 3 wants gone. This slice makes `verify`
a real state on the `remote-async` parameterization, so `delegate.join`'s "done"
**is** `jules.verify`'s "done": one machine, one recovery flow, no special-casing.
Today the base table (340) has no `verify` state and goes `working → completed`
directly — the seam below adds it.

## Design

### The parameterization registry (`data/parameterizations.json`)

A parameterization is a **named, monotone extension** of the base machine (340):
extra states, extra transitions, extra observers. Data, not code (CLAUDE.md
#8/#75; drift-tagged `# AGENCY-DRIFT: lifecycle-parameterizations`):

```json
{
  "default": { "states": [], "transitions": {}, "observers": [] },
  "remote-async": {
    "states": ["verify"],
    "transitions": { "working": ["verify"], "verify": ["completed", "input-required", "failed"] },
    "removes_from_base": ["working->completed"],
    "observers": ["jules.watch"]
  },
  "reviewed": {
    "states": ["in-review"],
    "transitions": { "working": ["in-review"], "in-review": ["completed", "input-required"] },
    "removes_from_base": ["working->completed"],
    "observers": ["gate.check"]
  }
}
```

> **`removes_from_base` is edge REPLACEMENT under the structural floor (panel
> F-2).** Not "monotone, never remove" (that framing was wrong — this slice
> legitimately replaces `working→completed`). The floor 340 enforces is
> *structural*: terminal base states stay terminal, and no base state is orphaned
> (unreachable from `submitted`). Replacing `working→completed` with
> `working→verify→completed` keeps `completed` reachable, so it passes. This
> encodes `COMPLETED ≠ done` precisely: verify is on the only path, not optional.

### `effective_table(parameterization)` and the open seam

- `ctx.lifecycle.open(..., parameterization="remote-async")` stamps the
  parameterization on the Lifecycle node (the 339 substrate prop).
- `ctx.lifecycle.move` (via 340's `_assert_transition`) reads
  `effective_table = extend_table(base, parameterizations[p])` — so a jules
  lifecycle's `move(→completed)` from `working` **raises** (must go through
  `verify`), while a `default` lifecycle's does not.

### The observer dispatch — `ctx.lifecycle.advance(lc)` (panel B2 + owner fork Q2)

The panel's #1 blocker was that `jules.verify` (a `role="transform"`) returns
`{done}` and **writes nothing**, and nothing calls it. The first fold put the call
in `delegate.join` — but the 2nd-pass panel (P2) showed that **hardcodes
`delegate`→`jules`** and doesn't generalize (the `reviewed` parameterization's
observer is `gate.check`, run by `subagent`). That is per-agent special-casing one
layer up — the very thing Goal 3 removes.

**Owner decision (Q2): one `advance()` reducer at the capability layer.** The
parameterization **declares its observer by name** (registry data); a single
reducer `ctx.lifecycle.advance(lifecycle_id)` looks it up and runs it through
`ctx.registry`, then performs the resulting move. Every driver caller calls the
SAME `advance` — none hardcodes jules/gate:

```jsonc
// parameterizations.json — the observer is declared, not hardcoded in a caller
"remote-async": { "states": ["verify"],
                  "transitions": {"working": ["verify"], "verify": ["completed","input-required","failed"]},
                  "observer": {"capability": "jules", "verb": "verify",
                               "on_done": "completed", "on_not_done": "input-required",
                               "on_error": "verify"} },   // N-3: lookup failure stays in verify
"reviewed":     { "states": ["in-review"],
                  "transitions": {"working": ["in-review"], "in-review": ["completed","input-required"]},
                  "observer": {"capability": "gate", "verb": "check", "on_done": "completed",
                               "on_not_done": "input-required"} }
```

The flow, uniform across agents:

1. A driver reports completion → its child enters **`verify`** / **`in-review`**
   (the driver's "completed" is `move(working→verify)`, NOT `→completed`).
2. Whoever reduces (`delegate.join`, `subagent.develop`) calls
   **`ctx.lifecycle.advance(child)`** — ONE call. `advance` reads the child's
   parameterization, invokes the declared `observer` via `ctx.registry`, and maps
   its verdict to a `move` (`on_done`/`on_not_done`/`on_error`).
3. So `delegate.join`'s "done" **is** the observer's "done" (N3 closed), and a
   *new* parameterization needs **zero caller edits** — it declares an observer and
   `advance` runs it. The `default` parameterization has no observer, so `advance`
   is a no-op and a local child reduces over raw `completed` as today.

> **Layering (panel P2 resolution).** `advance` is reachable as `ctx.lifecycle.
> advance` for ergonomics but is implemented at the **capability layer** (it calls
> out through `ctx.registry` to a capability verb like `jules.verify`, which needs
> `vcs`/network injection). The deep substrate (`agency/lifecycle.py`) never calls
> *into* a capability — that inversion is avoided. `advance` is the one place the
> pillar reaches its members, by declared name, never hardcoded.

### The 10 caps register, they don't reimplement

This slice does NOT rewrite `branch/delegate/jules/mode/persona/select/subagent/
workspace`. It gives them a **declaration seam**: a capability whose
`home == "lifecycle"` may expose a `parameterization` class attr (a key into the
registry). `jules` declares `parameterization = "remote-async"`; `subagent` (when
review-gated) declares `"reviewed"`. The dispatch path (`delegate.fan_out`,
Spec 040) passes that key to `lifecycle.open`. The wiring is one attr + one
argument — the drop-in bar.

> **Why this is the unifying model, not a feature.** Before this slice, "agent"
> was an implicit `Agent` node + a `PERFORMED_BY` edge, and the
> `home="lifecycle"` grouping was a documentation label. After it, *agent* is
> defined operationally — **the parameterization of the lifecycle it runs in** —
> exactly as CORE.md says. A remote agent and a local subagent differ not in
> their node type but in *which transitions and observers their lifecycle has*.

### What this slice does NOT do

- No rewrite of the 10 caps' verbs — only a `parameterization` attr + the open
  argument.
- No new observer daemons — observers reference existing watchers (`jules.watch`,
  `gate.check`).
- No per-parameterization side-effect hooks beyond wiring the observer (YAGNI
  until a third parameterization needs more — Spec 338 §"Scoped OUT").

## Acceptance (Gherkin)

```gherkin
Scenario: a remote-async lifecycle cannot complete without verify
  Given a Lifecycle opened with parameterization="remote-async" in state "working"
  When I call lifecycle.move(lid, to_state="completed")
  Then it raises IllegalTransition (must pass through "verify")
  When I move it working→verify→completed
  Then it succeeds (COMPLETED ≠ done is enforced)

Scenario: a default lifecycle completes directly
  Given a Lifecycle opened with parameterization="default" in state "working"
  When I call lifecycle.move(lid, to_state="completed")
  Then it succeeds (no verify required)

Scenario: a parameterization cannot orphan a terminal state
  Given a parameterization whose removes_from_base makes "completed" unreachable
  When the registry loads
  Then it is rejected (the floor holds)

Scenario: jules declares remote-async and dispatch wires it
  Given a jules dispatch via delegate.fan_out
  Then the child Lifecycle is opened with parameterization="remote-async"
  And its watch observer is jules.watch

Scenario: delegate.join and jules.verify agree on "done" (N3 — close the disconnect)
  Given a remote-async child Lifecycle whose run reports state "completed"
  But whose branch is NOT on origin (jules.verify → done=False)
  When delegate.join calls ctx.lifecycle.advance(child)
  Then advance runs the declared "jules.verify" observer and moves verify→input-required
  And the child is NOT counted done; join's "done" equals the observer's "done"

Scenario: advance is the ONE path — a new parameterization needs no caller edit (Q2/P2)
  Given a new parameterization "audited" declaring observer {capability:"X", verb:"y"}
  When any reducer calls ctx.lifecycle.advance(child)
  Then advance runs X.y via ctx.registry and moves per on_done/on_not_done
  And neither delegate.join nor subagent.develop is edited to add it

Scenario: verify lookup failure stays in verify, not failed (panel N-3)
  Given a remote-async child in "verify"
  When jules.verify's remote check errors (network/auth, ok=False)
  Then the child stays in "verify" (not "failed", not "completed")
  And delegate.join.done is False

Scenario (E2E, panel B5): the full remote-async round-trip across caps
  Given an intent and an injected vcs where branch "feat/x" IS on origin
  When delegate.fan_out dispatches a remote-async child for the item
  Then the child opens parameterization="remote-async" in "submitted"
  When the driver reports completion (move working→verify)
  And delegate.join runs jules.verify (branch present → done)
  Then the child moves verify→completed and join.done is True
  And a lifecycle_transition event trail exists for submitted→…→completed

Scenario: subagent uses the reviewed parameterization
  Given subagent.develop dispatches a child (parameterization="reviewed")
  When spec-review and quality-review gates both pass
  Then the child moves working→in-review→completed via lifecycle.move
  And subagent.develop:66's old raw update({"state":"completed"}) is gone
```

## Followup — Implementation Status (2026-06-21)

**SHIPPED** (branch `claude/lifecycle-342`). Re-grounded onto the **Spec 345
machine registry** that landed after this spec was drafted: a "parameterization"
IS a derived machine (no separate `parameterizations.json` — the registry is
`machines.json`). The unifying model holds end-to-end.

**Done:**
- **Observer declared as data, by name.** `machines.json` — `remote-async` gains
  `observer:{capability:"jules",verb:"verify",on_done:"completed",
  on_not_done:"input-required",on_error:"verify"}`; new `reviewed` machine
  (`working→in-review→{completed,input-required}`) declares `gate.check`.
  `resolve_machine`/`_normalise`/`_apply_delta` carry `observer` through the
  `derives` chain (`agency/_lifecycle_machines.py`).
- **The ONE reducer (owner fork Q2).** `ctx.lifecycle.advance(lc_id)`
  (`agency/lifecycle.py`) reads the child's machine observer, runs it
  **generically through `engine.registry.invoke`** (never a hardcoded jules/gate
  import — the deep substrate reaches members only by declared name; observer args
  built from the verb signature + node props, `state="completed"` implied by the
  observer source state derived via `_observer_source_state`), and maps the
  verdict → a `move`: `done`→`on_done`; `done=False`+`error`→`on_error` (**stays in
  `verify`**, panel N-3); else→`on_not_done`. No observer (default `a2a`) → no-op.
  A new parameterization needs **zero caller edits**.
- **Declaration seam.** `Capability.parameterization` class-attr (carried through
  `as_capability`); `jules.parameterization="remote-async"`,
  `subagent.parameterization="reviewed"`.
- **The two "done"s become one (B2/N3).** `delegate.fan_out` derives the child's
  machine from the **driver's** declared parameterization (replacing the old
  hardcoded `"remote-async"` constant) + stamps the observer's `branch` via new
  `lifecycle.annotate`; `delegate.join` calls `advance` per child before reducing,
  so join's "done" IS `jules.verify`'s "done".
- **subagent through the reviewed machine (B-scenario).** `subagent.develop` opens
  the child `reviewed` and drives `working→in-review→completed` via the SOLE state
  writer `lifecycle.move` — the raw `Lifecycle().close()` at `:66` is gone (the
  reviewed machine forbids `working→completed` directly, proving the gate path).
- **Latent 345 gap fixed.** `_declared_states` widens the `(Lifecycle,state)`
  ontology enum with a derived machine's `add_states`/`replace` targets, so a
  `move` to `verify`/`in-review` passes validation (was rejected — the state never
  reached the enum union).

**Tests:** 11 acceptance scenarios in
`tests/acceptance/features/lifecycle_parameterization.feature` (cannot complete
without verify; default completes directly; observer declared by name; jules
declares the param; fan_out wires it; advance completes / →input-required /
stays-in-verify-on-error; default no-op; new-param-no-caller-edit; join==observer
done). The pre-existing `delegate fan_out` lifecycle scenario reframed (a local
`reflect` driver → default parameterization, not the old hardcoded constant).
Drift + no-truncate + doc-drift clean; install regenerated.

**Not done (out of this slice):** the `default` lifecycle E2E with an injected
vcs is exercised via the unit-level advance scenarios rather than a separate
full-stack `Background` (the fan_out→join→advance path IS the cross-cap e2e). No
new observer daemons (YAGNI per spec §"What this slice does NOT do").
