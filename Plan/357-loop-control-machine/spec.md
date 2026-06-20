---
spec_id: "357"
slug: loop-control-machine
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [3, 4]
depends_on: ["338", "339", "340", "342", "345", "353", "355", "356"]
parent_spec: "353"
domain: loop / lifecycle
wave: looper-port
---

# Spec 357 — The loop control machine (a derived Lifecycle state machine)

> Child of Spec 353. Ports looper's **loop runtime + `loop_control` +
> `references/control-rubric.md`**, and the in-session execution contract
> (`RUN_IN_SESSION.md`). Spec 345 made the Lifecycle pillar *any* state machine;
> 357 registers the `loop` machine and the termination evaluator. **The loop's
> in-session runtime IS this machine being walked** — `state.json` / `run-log.md`
> evaporate into graph reads.

## Why

Looper's runner (`templates/run-loop.py`) walks a fixed shape: gather context →
host drafts `plan.md` → **plan gate** (revise ≤ N) → host writes `delivery-N.md` →
**delivery gate** (revise ≤ N) → stop on pass / cap / no-progress. It enforces
`loop_control`:

```yaml
loop_control:
  max_iterations: 12
  budget: { usd: 5.00, tokens: 2_000_000, wall_clock_min: 30 }
  no_progress: { max_stalled_iterations: 2, action: stop }   # same blocker repeats
  human_checkpoints: [after_plan]
  stop_conditions: ["all deliveries pass clean", "max_iterations reached",
                    "same blocker repeats for 2 iterations", "any budget cap exceeded"]
```

> Looper's design principle #6 ("honest durability") and its own README are blunt:
> looper is a **scaffolder + session handoff, not a durable orchestration
> engine.** 357 honours that boundary — it provides the machine, the guards, and
> gate-level resume (graph-backed), and explicitly does **not** promise step-level
> checkpoint/restart, concurrency control, or a production run history. The
> `execution.mode: orchestrated` escape hatch (hand off to a real orchestrator)
> stays a named non-goal, exactly as in looper.

In agency this is not bespoke control flow — it is a **registered Lifecycle
machine** (Spec 345) plus a **termination evaluator**. `Lifecycle.open/move/close`
(`agency/lifecycle.py`) is already the guarded sole state writer; `move` validates
against the per-machine transition table. 357 adds the `loop` machine and a
`control_gate` that the machine consults before each `move`.

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

Registering this is **data, not an engine edit** (the drop-in bar, master §Done
When). The orphan/terminal floor (340/345) holds at load. `# AGENCY-DRIFT:
lifecycle-machines` tags the entry.

### `open_loop` mints a `Lifecycle{machine:"loop"}` + `LoopControl`

```python
@verb(role="effect")
def open_loop(self, ctx, goal_id: str, *, max_iterations: int = 12, max_revisions: int = 3,
              budget: dict | None = None, no_progress_stall: int = 2,
              human_checkpoints: list[str] | None = None) -> dict:
    """Open a loop: a Lifecycle on the "loop" machine, SERVING the goal's Intent.

    Records a LoopControl node (the termination guards). REFUSES to open if any
    revise_until_clean gate lacks a verdict source (delegates to
    loop.recommend_council, 356). Returns {loop_id, lifecycle_id, state:"planning"}.
    chain_next: loop.advance to walk it.
    """
    # ctx.lifecycle.open(ctx.intent_id, machine="loop")  — the pillar write frame
```

`max_iterations` / `max_revisions` / `budget` (`usd` / `tokens` / `wall_clock_min`)
/ `no_progress_stall` / `human_checkpoints` are the looper `loop_control`,
recorded on a `LoopControl` node. **`open_loop` enforces the master invariant:** it
will not open a loop with a termination-guard-free control (looper "won't emit a
loop with no termination guard").

### `advance` is the only mover; `control_gate` guards every transition

```python
@verb(role="effect")
def advance(self, ctx, loop_id: str, *, artefact: str = "") -> dict:
    """Advance the loop one transition (the in-session walk step). Reads the
    current state, runs the relevant gate's criteria (loop.check, 355) +
    council (loop.convene, 356), then asks control_gate whether a move is
    still permitted, then ctx.lifecycle.move(...) to the next state.

    Returns {state, decision, stop_reason?, review?}. chain_next: advance again
    until a terminal state, or stop_reason is set.
    """
```

The per-state behaviour mirrors looper's `run()`:

| From state | Gate run (355/356) | On pass | On revise | Guard (control_gate) |
|---|---|---|---|---|
| `planning` | — (host drafts plan artefact) | → `plan_gate` | — | budget/wall-clock |
| `plan_gate` | plan criteria + council verdict | → `delivering` | → `planning` (revision++) | `max_revisions`, `no_progress` |
| `delivering` | — (host writes delivery-N) | → `delivery_gate` | — | `max_iterations`, budget |
| `delivery_gate` | delivery criteria + council verdict | → `completed` | → `delivering` (iteration++) | `max_revisions`, `no_progress` |

The "host drafts the artefact" step runs natively via `ctx.host` sampling (Spec
285) or a delegated host driver (356); the external runner (360) does the same via
argv. Either way the artefact is recorded as a `LoopArtefact` (kind plan/delivery/
review), so resume is a graph read, not a `state.json` parse.

### `control_gate` — the termination evaluator (ports looper's guards)

A pure evaluator (a `gate`, Spec 328 shape) consulted before each `move`:

```python
def control_gate(control: LoopControl, history: list[Transition]) -> dict:
    """Return {permit: bool, stop_reason: str|""}. Ports run-loop.py guards:
      - max_revisions: revisions into a gate's predecessor exceed the cap → stop("max_revisions")
      - max_iterations: delivery cycles exceed the cap → stop("max_iterations")
      - no_progress: the SAME failure signature repeats max_stalled_iterations
        times at the same gate → stop("no_progress")   (looper no_progress_reached)
      - budget: wall_clock_min elapsed, or usd/tokens estimate exceeded → stop("budget")
      - human_checkpoints: state ∈ checkpoints → pause for elicit (Spec 285)
    """
```

- **no-progress** reuses looper's signature comparison: a failure-set hash per
  gate; if it repeats `max_stalled_iterations` times, stop (or, with
  `action: human_checkpoint`, pause for an override — both ported).
- **budget** wall-clock is measured against the lifecycle's `opened_at`; usd/token
  caps are estimates recorded as evidence (agency does not bill, so these are
  advisory stop signals, honest about being estimates — `CLAUDE.md` rule 8: no
  fake precision).
- **stop_conditions** are *derived* from the control fields, not authored twice
  (derivability audit) — `loop.stop_reason(loop_id)` renders them for `LOOP.md`.

### `loop_status` / `stop_reason` — observability for free

```python
@verb(role="transform")
def loop_status(self, ctx, loop_id: str) -> dict:
    """The loop's live state from the graph: current machine state, iteration,
    revision counts per gate, last verdict, artefacts produced, stop_reason if
    terminal. This is looper's state.json + run-log.md — but READ from
    provenance, never written by hand. chain_next: advance, or compile (359)."""
```

Looper's `state.json` (status/iteration/no_progress/consent) and `run-log.md`
(append-only step log) are both **derived** from the Lifecycle transitions + the
`LoopArtefact` / gate ledger nodes. The export (359) renders them back to files
for the portable workspace.

## Acceptance (Gherkin)

```gherkin
Scenario: the loop machine is registered and floor-valid
  When the lifecycle registry loads
  Then a machine "loop" exists with initial "planning" and terminals completed/failed/canceled
  And no loop state is orphaned from "planning" (the 340/345 floor holds)

Scenario: open_loop refuses a termination-guard-free loop
  When I open_loop with max_iterations 0 and no budget and no caps
  Then it refuses (looper: never emit a loop with no termination guard)

Scenario: open_loop refuses a revise_until_clean gate with no verdict source
  Given a plan gate revise_until_clean with only reviewers (356)
  When I open_loop
  Then it refuses citing the missing verdict_source

Scenario: a clean plan advances to delivering
  Given an open loop whose plan criteria pass and judge verdict is pass
  When I advance from plan_gate
  Then the state moves to delivering

Scenario: a revise verdict loops back and counts a revision
  Given a plan_gate judge verdict revise
  When I advance
  Then the state returns to planning and the revision count increments

Scenario: max_revisions stops the loop
  Given a plan_gate that has revised max_revisions times with the same failures
  When I advance
  Then control_gate denies the move and stop_reason is "max_revisions"

Scenario: no-progress stops on a repeated blocker
  Given a delivery_gate failing with the same signature for max_stalled_iterations
  When I advance
  Then stop_reason is "no_progress"

Scenario: a human checkpoint pauses the walk
  Given human_checkpoints includes "after_plan" and no host bound
  When the plan passes its gate
  Then advance returns a typed input-required pause before delivering

Scenario: status and stop conditions are read from the graph
  Given a loop that ran two delivery iterations
  When I loop_status
  Then iteration counts and artefacts come from provenance with no state.json written
```

## Done When

- [ ] The `loop` machine is registered in `machines.json` (data only; no engine edit) and passes the per-machine floor.
- [ ] `loop.open_loop` mints `Lifecycle{machine:"loop"}` + `LoopControl`, refuses guard-free and verdict-source-less loops.
- [ ] `loop.advance` is the sole mover; per-state behaviour matches the table; artefacts recorded as `LoopArtefact`.
- [ ] `control_gate` ports max_revisions / max_iterations / no_progress / budget / human_checkpoints.
- [ ] `loop.loop_status` + `loop.stop_reason` derive state from provenance (no hand-written state.json in-session).
- [ ] `control-rubric.md` ships verbatim under `data/rubrics/`.
- [ ] `tests/acceptance/test_loop_machine.py` covers the scenarios.
- [ ] `TODO.md` row updated.

## Followup — Implementation Status (2026-06-20)

**Verdict:** Not started — drafted under the 353 wave. The loop runtime as a
registered Lifecycle machine (345) walked by `advance`, guarded by a
`control_gate` that ports looper's termination logic; `state.json`/`run-log.md`
derived from provenance. Honest-durability boundary preserved (gate-level resume,
no orchestration promises). Depends on 355 (gate criteria) + 356 (council verdict);
consumed by the wizard (358) and emission (359).
