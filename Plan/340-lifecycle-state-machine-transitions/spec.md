---
spec_id: "340"
slug: lifecycle-state-machine-transitions
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 4]
depends_on: ["075", "338", "339"]
domain: lifecycle
wave: program-master
parent_spec: "338"
---

# Spec 340 — Enforced A2A transition table (the state machine)

> Child of the Lifecycle-pillar deep program (Spec 338). Hardens `lifecycle.move`
> (Spec 339) with an **enforced transition table** so the A2A state machine stops
> being decorative: any state can no longer jump to any state.

## Why

`ontology.py:58 LifecycleState` constrains the *value* of `state`, but Spec 338
§Why item 2 documents the real defect — **no transition is enforced**. Once 339
makes `move` the sole writer, the column has one chokepoint; this slice puts a
guard at that chokepoint. The A2A alignment (CORE.md §3 — "states align with A2A
tasks") is only meaningful if `completed → working`, `submitted → completed`
(skipping `working`), and `canceled → submitted` are **rejected**. Provenance
that records a `completed` Lifecycle reached without passing `working` lies about
what happened (Goal 2).

## Design

### The transition table (definable registry — `data/transitions.json`)

Per CLAUDE.md #8 (no hardcoded values) and #75 (definable registries like
`shell.define`), the base table is **data**, not code branches:

```json
{
  "submitted":      ["working", "canceled"],
  "working":        ["input-required", "auth-required", "completed", "failed", "canceled"],
  "input-required": ["working", "canceled"],
  "auth-required":  ["working", "canceled"],
  "completed":      [],
  "failed":         ["working", "canceled"],
  "canceled":       []
}
```

Loaded once, drift-tagged (`# AGENCY-DRIFT: lifecycle-transitions`), overridable
via a graph-stored `TransitionTable` node (the `shell.define` pattern, Spec 075 —
graph-first read, seed fallback). The keys/values are validated against
`LIFECYCLE_STATES` at load (a typo in the data is a startup error, not a silent
gap).

### The guard (`clusters/_base.py::_assert_transition`)

```python
def _assert_transition(self, from_state, to_state, *, table=None):
    """Raise IllegalTransition unless to_state is reachable from from_state
    in the (possibly parameterization-extended) table. Terminal states have
    an empty allow-list — nothing leaves them."""
```

`lifecycle.move` (339) calls this BEFORE writing. The error is a typed
`IllegalTransition` (Spec 001 typed-errors) carrying `{from_state, to_state,
allowed}` so the caller (or the AskUser re-entry loop, 343) can react. `close`
inherits the guard through `move`.

### Parameterization-aware (the 342 seam, stubbed here)

`_assert_transition(table=…)` accepts an *effective* table — the base table
**monotonically extended** by a parameterization (Spec 342): a parameterization
may add states/edges (remote-async inserts `verify`; `working → verify →
completed`) but may **never remove** a base edge. 340 ships the base table + the
`table=` parameter + a monotonicity check (`extend_table(base, extra)` asserts
`base ⊆ effective`); 342 supplies the variant data. The safety floor — terminal
states stay terminal, no parameterization can make `completed → working` legal —
is enforced here (the override path validates against an invariant set).

### What this slice does NOT do

- No parameterization *data* (342 supplies the variant sets; 340 only proves the
  extension mechanism is monotone + floor-safe).
- No change to the verb surface (339 owns it); this is the guard behind `move`.

## Acceptance (Gherkin)

```gherkin
Scenario: a legal transition succeeds
  Given an open Lifecycle in state "submitted"
  When I call lifecycle.move(lid, to_state="working")
  Then the Lifecycle state is "working"

Scenario: an illegal transition raises
  Given an open Lifecycle in state "completed"
  When I call lifecycle.move(lid, to_state="working")
  Then it raises IllegalTransition with allowed=[]

Scenario: a skip transition raises
  Given an open Lifecycle in state "submitted"
  When I call lifecycle.move(lid, to_state="completed")
  Then it raises IllegalTransition (working not yet reached)

Scenario: the table is data-driven and overridable
  Given a TransitionTable override node in the graph
  Then lifecycle.move reads the override, not the seed
  And the override cannot remove a base edge (monotone) nor make a terminal non-terminal

Scenario: the seed table is internally consistent
  Then every state in transitions.json is a valid LifecycleState
  And every target is a valid LifecycleState
```

## Followup — Implementation Status (2026-06-20)

Not started. Adds `data/transitions.json` + `_assert_transition` behind 339's
`move`. The three former unguarded writes (routed through `move` in 339) inherit
enforcement automatically. Parameterization variant data lands in 342.
