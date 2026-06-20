---
spec_id: "342"
slug: agent-as-lifecycle-parameterization
status: draft
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

CORE.md §3: *"An agent (the old 'who') is a Lifecycle parameterization — an
agent-session is a lifecycle whose transitions/observers differ (a remote async
agent inserts `verify`; `COMPLETED ≠ done`)."* Ten capabilities declare
`home = "lifecycle"` (`branch · delegate · gate · jules · mode · persona · select
· subagent · workspace` + the implicit session) — each *parameterizes how work
proceeds* — but Spec 338 §Why item 4 documents that there is **no Lifecycle they
parameterize**. The richest case is concrete and currently impossible to express:
a **remote async agent** (jules, Spec 012) must not be `completed` when its run
returns — its output needs `verify` first (`COMPLETED ≠ done`). The base
transition table (340) has no `verify` state and goes `working → completed`
directly. Without a parameterization seam, the substrate cannot encode the single
most important async-agent invariant in the canon.

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

> **`removes_from_base` is the ONE narrow exception to monotonicity** and it is
> *safety-tightening*, never loosening: a parameterization may remove a base edge
> only to **force** an inserted intermediate (drop `working→completed` so
> `completed` is reachable *only* via `verify`). The floor (340) still holds —
> terminal states stay terminal, and a removal that would orphan `completed`
> (make it unreachable) is rejected at load. This encodes `COMPLETED ≠ done`
> precisely: not "verify is optional" but "verify is on the only path".

### `effective_table(parameterization)` and the open seam

- `lifecycle.open(..., parameterization="remote-async")` stamps the
  parameterization on the Lifecycle node (the 339 optional prop).
- `lifecycle.move` (via 340's `_assert_transition`) reads
  `effective_table = extend_table(base, parameterizations[p])` — so a jules
  lifecycle's `move(→completed)` from `working` **raises** (must go through
  `verify`), while a `default` lifecycle's does not.
- Observers in the parameterization wire `lifecycle.watch` (341) to the right
  watcher (`jules.watch` for remote-async; `gate.check` for reviewed).

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
```

## Followup — Implementation Status (2026-06-20)

Not started. Adds `data/parameterizations.json` + `effective_table`/`extend_table`
+ the `parameterization` declaration attr on `home="lifecycle"` caps. Realizes
CORE.md §3's "agent = Lifecycle parameterization" and the `COMPLETED ≠ done`
invariant for remote-async agents. The 10 caps register, they do not reimplement.
