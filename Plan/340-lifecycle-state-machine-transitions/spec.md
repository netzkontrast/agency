---
spec_id: "340"
slug: lifecycle-state-machine-transitions
status: partial
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 4]
depends_on: ["075", "338", "339"]
domain: lifecycle
wave: program-master
parent_spec: "338"
---

# Spec 340 — Enforced A2A transition table (the state machine)

> Child of the Lifecycle-pillar deep program (Spec 338). Hardens the **substrate**
> `agency/lifecycle.py::Lifecycle.move` (Spec 339 — Lifecycle is a *pillar*, not a
> capability) with an **enforced transition table** so the A2A state machine stops
> being decorative: any state can no longer jump to any state.
>
> **Panel folds (2026-06-20):** the safety property is the **orphan/terminal
> floor**, not "monotone, never remove an edge" (F-2) — a parameterization (342)
> may *replace* `working→completed` with `working→verify→completed`; the load-check
> rejects only (a) an out-edge from a terminal base state and (b) a base state made
> unreachable from `submitted`. The transition data lives at
> `agency/_lifecycle_data/transitions.json` (substrate), not in a capability folder.
> The **sole-writer invariant (B3)** is guarded statically: `# AGENCY-DRIFT:
> lifecycle-state-writer` + a `scripts/check-drift` grep that fails CI on any
> `update(...{"state"` / `record("Lifecycle"` / `record("SessionLifecycle"` outside
> `agency/lifecycle.py`.

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

**Partial — Slice 1 SHIPPED 2026-06-20.** The enforced table lands behind 339's
`move`; the build-order note (after 340 → 344) is moot now that both are in (344
shipped first per owner request; the guard layered in cleanly without touching the
emit path).

Done:
- `agency/_lifecycle_data/transitions.json` — the base A2A table as **data**
  (`# AGENCY-DRIFT: lifecycle-transitions`), validated against `LIFECYCLE_STATES`
  at load (a typo is a startup error).
- `agency/_lifecycle_transitions.py` — pure module: typed `IllegalTransition`
  (`{from_state, to_state, allowed}`), `load_base_table`, `assert_transition`,
  `extend_table` (monotone union + terminal-floor: a graph override can never
  remove a base edge nor reopen a terminal state), `terminal_states`.
- `Lifecycle.move` (the SOLE writer) calls `assert_transition(current, to_state,
  self._effective_table())` before writing — so the three routed writers
  (delegate/gate/lifecycle_gate) inherit enforcement for free. `_effective_table`
  reads the graph override (`Artefact{kind:"transition-table"}`, the `shell.define`
  pattern) per-move, seed fallback. A well-formed lifecycle is guarded; a
  state-less legacy node is exempt (can't be reasoned about).
- 6 acceptance scenarios (legal succeeds · terminal→illegal with `allowed=[]` ·
  skip raises · seed table internally consistent · override read + floor-safe ·
  override can't reopen a terminal). Full suite green.

**Table refinement (grounded, not a magic-number edit — CLAUDE.md #8).** The spec
sketch's `submitted: [working, canceled]` rejected `submitted→input-required`,
which broke 15 real consumer gate tests (music/prompt): a **readiness/pre-flight
gate fires before work starts** and pauses a freshly-opened (`submitted`)
lifecycle. So `submitted` also reaches `input-required`/`auth-required`. The core
invariant the spec defends — *no `completed` without passing `working`* — is
intact (`submitted` still can NOT skip to `completed`/`failed`).

Still (Slice 2): the **B3 static drift guard** (`scripts/check-drift` grep that
fails CI on any `update(...{"state"` / `record("Lifecycle"` outside
`agency/lifecycle.py`) is deferred to **339b** — `subagent`/`music` still write
`state` directly, so the guard would red CI today; it lands once those writers are
routed through `move`. Parameterization *variant data* (the `verify`-insert) lands
in **342** (340 only proves the extension mechanism is monotone + floor-safe). The
reachability/orphan check (F-2 b) activates when 342 supplies replacement edges.
