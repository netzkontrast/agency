<!-- agency-node: spec-366 -->
---
spec_id: "366"
slug: loop-control-machine
status: draft
last_updated: 2026-06-21
owner: "@agency"
vision_goals: [3, 4]
depends_on: ["338", "339", "340", "342", "344", "345", "349", "362", "364", "365"]
parent_spec: "362"
affects:
  - agency/_lifecycle_data/machines.json   # register the "loop" machine (the 345 data-seam)
  - agency/_loop.py                         # open / advance reducer + control_evaluate (the guards)
  - agency/_lifecycle_data/loop/rubrics/    # control-rubric.md (verbatim from looper)
domain: loop / lifecycle-spine
wave: looper-port
---

# Spec 366 — The loop control machine (a registered Lifecycle machine + a guard)

> Child of Spec 362. **Spine-framed (2026-06-21):** the loop's in-session runtime
> IS a machine on the lifecycle spine being walked. Spec 345 already made the
> pillar *any* state machine; 366 registers the `loop` machine in `machines.json`
> (data) and adds the **termination evaluator** in `agency/_loop.py`. `state.json`
> / `run-log.md` evaporate into graph reads (Spec 341 + the 344/349b event bus).
> **No new capability** — the walk is the pillar `ctx.lifecycle.open/move`; the
> loop-specific control flow is functions in the one spine module.

## Why

Looper's runner walks a fixed shape — gather context → draft `plan.md` → **plan
gate** (revise ≤ N) → write `delivery-N.md` → **delivery gate** (revise ≤ N) →
stop on pass/cap/no-progress — enforcing `loop_control`:

```yaml
loop_control:
  max_iterations: 12
  budget: { usd: 5.00, tokens: 2_000_000, wall_clock_min: 30 }
  no_progress: { max_stalled_iterations: 2, action: stop }
  human_checkpoints: [after_plan]
```

> Looper is honest (its principle #6): a **scaffolder + handoff, not a durable
> orchestrator**. 366 keeps that boundary — it provides the machine, the guards,
> and **gate-level resume** (graph-backed, via Spec 343 `lifecycle.resume`), and
> does NOT promise step-level checkpoint/restart, concurrency, or a production run
> history. The `execution.mode: orchestrated` escape hatch stays a named non-goal.

In agency this is not bespoke control flow — it is a **registered Lifecycle
machine** (345) plus a **termination evaluator**. `Lifecycle.open/move/close`
(`agency/lifecycle.py`) is already the guarded sole state writer; `move` validates
the per-machine table and **emits on the event bus** (344/349b).

## Design

### The `loop` machine (data in `machines.json` — Spec 345)

```jsonc
"loop": {
  "initial": "planning",
  "states": ["planning","plan_gate","delivering","delivery_gate","completed","failed","canceled"],
  "transitions": {
    "planning":      ["plan_gate","canceled","failed"],
    "plan_gate":     ["planning","delivering","failed","canceled"],   // revise→planning | pass→delivering
    "delivering":    ["delivery_gate","canceled","failed"],
    "delivery_gate": ["delivering","completed","failed","canceled"],  // revise→delivering | pass→completed
    "completed": [], "failed": [], "canceled": []
  },
  "terminal": ["completed","failed","canceled"]
}
```

Registering this is **data, not an engine edit** (`# AGENCY-DRIFT:
lifecycle-machines`). The orphan/terminal floor (340/345) holds per machine at
load; the 347 frugal floor invariant applies (no path skips a required floor gate).

### `_loop.open` — open the machine + record the control (no new verb)

```python
def open(ctx, goal_id, *, max_iterations=12, max_revisions=3, budget=None,
         no_progress_stall=2, human_checkpoints=None) -> dict:
    """ctx.lifecycle.open(ctx.intent_id, machine="loop") SERVING the goal's Intent,
    + record the termination guards (on the Lifecycle node / a linked control).
    REFUSES to open a guard-free loop, or one whose revise_until_clean gate lacks
    a verdict source (delegates to 365). Returns {loop_id, state:"planning"}."""
```

Enforces the master invariant: **never open a loop with no termination guard**
(looper) and **never with a verdict-source-less gate** (the reviewer-only rule,
365). Called by the wizard's control phase (367 phase 5).

### `_loop.advance` — the walk reducer; the guard runs before every move

```python
def advance(ctx, loop_id, *, artefact="") -> dict:
    """Advance one transition (the in-session walk step). Read the current state,
    run the relevant gate's criteria (gate.check, 364) + council (panel.convene,
    365), ask control_evaluate whether a move is still permitted, then
    ctx.lifecycle.move(...). Returns {state, decision, stop_reason?, review?}."""
```

Per-state behaviour mirrors looper's `run()`:

| From state | Gate (364/365) | On pass | On revise | Guard (control_evaluate) |
|---|---|---|---|---|
| `planning` | — (host drafts the plan artefact) | → `plan_gate` | — | budget/wall-clock |
| `plan_gate` | plan criteria + council verdict | → `delivering` | → `planning` (revision++) | `max_revisions`, `no_progress` |
| `delivering` | — (host writes delivery-N) | → `delivery_gate` | — | `max_iterations`, budget |
| `delivery_gate` | delivery criteria + council verdict | → `completed` | → `delivering` (iteration++) | `max_revisions`, `no_progress` |

"Host drafts the artefact" runs natively via `ctx.host` sampling (Spec 285) or a
delegated host driver (365); the external runner (369) does the same via argv.
Either way the artefact is recorded (a graph node), so resume is a graph read.

### `control_evaluate` — the termination evaluator (ports looper's guards)

A pure function in `_loop.py`, consulted before each `move`:

```python
def control_evaluate(control, history) -> dict:
    """Return {permit, stop_reason}. Ports run-loop.py guards:
      - max_revisions: revisions into a gate's predecessor exceed the cap → stop
      - max_iterations: delivery cycles exceed the cap → stop
      - no_progress: the SAME failure signature repeats max_stalled_iterations
        at the same gate → stop (looper no_progress_reached)
      - budget: wall_clock_min elapsed (from the Lifecycle's opened_at), or
        usd/tokens estimate exceeded → stop (advisory estimates, no fake precision)
      - human_checkpoints: state ∈ checkpoints → pause for elicit (Spec 285)
    """
```

`no_progress` reuses looper's failure-signature comparison. `stop_conditions` are
**derived** from the control fields, not authored twice (derivability) — rendered
for `LOOP.md` by 368.

### Status & stop reason — reuse `manage` (341), no new verbs

Looper's `state.json` (status/iteration/no_progress/consent) and `run-log.md`
(step log) are **derived** from the Lifecycle transitions + the 344 event trail:
`manage.lifecycle(loop_id)` (current rolled-up state) and
`manage.lifecycle_trail(loop_id)` (the transition history with `stop_reason` as
move evidence). The export (368) renders them back to files for the portable
workspace.

## Acceptance (Gherkin)

```gherkin
Scenario: the loop machine is registered and floor-valid
  When the lifecycle registry loads
  Then a machine "loop" exists with initial "planning" and terminals completed/failed/canceled
  And no loop state is orphaned from "planning" (the 340/345 floor holds)

Scenario: open refuses a termination-guard-free loop
  When I open a loop with max_iterations 0 and no budget and no caps
  Then it refuses (looper: never emit a loop with no termination guard)

Scenario: open refuses a revise_until_clean gate with no verdict source
  Given a plan gate revise_until_clean with only reviewers (365)
  When I open the loop
  Then it refuses citing the missing verdict_source

Scenario: a clean plan advances to delivering
  Given an open loop whose plan criteria pass and judge verdict is pass
  When I advance from plan_gate
  Then ctx.lifecycle.move takes the state to delivering

Scenario: a revise verdict loops back and counts a revision
  Given a plan_gate judge verdict revise
  When I advance
  Then the state returns to planning and the revision count increments

Scenario: max_revisions stops the loop
  Given a plan_gate revised max_revisions times with the same failures
  When I advance
  Then control_evaluate denies the move and stop_reason is "max_revisions"

Scenario: no-progress stops on a repeated blocker
  Given a delivery_gate failing with the same signature for max_stalled_iterations
  When I advance
  Then stop_reason is "no_progress"

Scenario: status and stop conditions are read from the graph
  Given a loop that ran two delivery iterations
  When I manage.lifecycle / manage.lifecycle_trail it
  Then iteration counts and stop_reason come from provenance with no state.json written
```

## Done When

- [ ] The `loop` machine is registered in `machines.json` (data only; no engine edit) and passes the per-machine floor.
- [ ] `_loop.open` mints `Lifecycle{machine:"loop"}` + records the control; refuses guard-free and verdict-source-less loops.
- [ ] `_loop.advance` is the sole walk reducer (moves via `ctx.lifecycle.move`); per-state behaviour matches the table; artefacts recorded.
- [ ] `control_evaluate` ports max_revisions / max_iterations / no_progress / budget / human_checkpoints.
- [ ] Status/stop_reason derive from provenance via `manage.lifecycle`/`lifecycle_trail` (341) — no hand-written state.json in-session.
- [ ] `control-rubric.md` ships verbatim under `agency/_lifecycle_data/loop/rubrics/`.
- [ ] `tests/acceptance/test_loop_machine.py` covers the scenarios.
- [ ] `TODO.md` row updated.

## Followup — Implementation Status (2026-06-21)

**Verdict:** Re-drafted spine-framed (2026-06-21). The loop runtime as the `loop`
machine (data, the 345 seam) walked via the pillar `ctx.lifecycle.open/move`,
with the loop-specific control flow (`open`/`advance`/`control_evaluate`) in the
one `_loop.py` module; `state.json`/`run-log.md` derived from provenance
(`manage` 341 + the 344/349b event bus). Honest-durability boundary preserved
(gate-level resume via 343, no orchestration promises). **Frugal: net-new is the
machine entry (data) + the `_loop.py` reducer + control-rubric (data) — no new
capability verbs.** Depends on 364 (gate criteria) + 365 (council verdict);
consumed by the wizard (367) and emission (368).
