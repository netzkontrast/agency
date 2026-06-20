---
spec_id: "339"
slug: lifecycle-capability-write-frame
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 4]
depends_on: ["016", "024", "080", "290", "338"]
domain: lifecycle
wave: program-master
parent_spec: "338"
---

# Spec 339 — `lifecycle` capability scaffold + the write frame (`open · move · close`)

> Child of the Lifecycle-pillar deep program (Spec 338). The **foundation
> slice**: it lands the `lifecycle` package and the canonical *write* frame, and
> makes `move` the **sole writer** of `Lifecycle.state`. The transition table
> (340), observe suite (341), and parameterization (342) are pure additions onto
> this scaffold.

## Why

Spec 338 §Architecture calls for a `lifecycle` capability that owns the
CORE.md §3 verb frame. Today a `Lifecycle` node is born as a side-effect
(`develop.session_start` mints `SessionLifecycle`; the invocation pipeline records
`Invocation`/`Agent`) and its `state` is written by three **unguarded**
`memory.update` sites (`gate.check`, the `lifecycle_gate` substrate tool, and
`reflect`). Before any transition *enforcement* (340) can land, the **write frame
must exist and own the state column**: one verb opens a Lifecycle, one verb moves
it, one verb closes it — and `move` is the single chokepoint every state change
flows through. This slice is thin on enforcement (340 adds the table) and complete
on **ownership**: after it, nothing outside `lifecycle.move` writes `state`.

## Design

### Package layout (mirrors `agency/capabilities/discover/`, Spec 308)

```
agency/capabilities/lifecycle/
  __init__.py            # exports LifecycleCapability; re-home anchor for Spec 291
  _main.py               # LifecycleCapability(CapabilityBase): name="lifecycle", home="lifecycle"
  ontology.py            # lifecycle_ontology = OntologyExtension(...) — reuses the core Lifecycle node
  clusters/
    __init__.py
    _base.py             # LifecycleCluster mixin: _recall, _serving, _assert_transition (stub → 340)
    machine.py           # open · move · close
  data/                  # transitions.json lands in 340
  templates/
    lifecycle-board.md   # Spec 292 convergence Document (populated by 341/343)
  references/
    state-machine.md     # <!-- doc-source: agency/capabilities/lifecycle/clusters/machine.py -->
```

`_main.py` carries the capability docstring that derives the SkillDoc (Spec 080):
*Use when:* a task/agent session's state must be opened, advanced, or closed
deliberately; *Triggers:* starting a unit of work that has a lifecycle, a gate
that must pause work, a session that reaches a terminal state; *Red flags:*
writing `Lifecycle.state` by hand via `memory.update` → use `lifecycle.move`.

### The write verbs (`clusters/machine.py`)

```python
@verb(role="act")
def open(self, intent_id: str, kind: str = "task", agent_id: str = "",
         parameterization: str = "") -> dict:
    """Mint a Lifecycle SERVING the intent in state `submitted`.

    Records a Lifecycle node {state: "submitted", phase: "", kind,
    parameterization} + a SERVES edge to the intent; optional agent_id
    adds a PERFORMED_BY edge (idempotent Agent upsert, mirroring
    _invoke.InvocationRecorder.open). Returns {lifecycle_id, state}.
    """

@verb(role="act")
def move(self, lifecycle_id: str, to_state: str, evidence: str = "") -> dict:
    """The SOLE writer of Lifecycle.state. Transition the lifecycle to
    `to_state`, recording evidence. In 339 it validates the value against
    the LifecycleState enum and refuses a no-op; 340 adds the full
    transition-table guard via _base._assert_transition. Returns
    {lifecycle_id, from_state, to_state}."""

@verb(role="act")
def close(self, lifecycle_id: str, outcome: str = "completed",
          evidence: str = "") -> dict:
    """Terminal move to completed | failed | canceled (delegates to
    move(), inheriting the guard). Returns {lifecycle_id, state, outcome}."""
```

`open` REUSES the `_invoke.InvocationRecorder.open` agent-upsert pattern (rule 2 —
one way to mint a performer). `close` is `move` to a terminal state — not a
parallel writer.

### Route the three unguarded writes through `move` (the ownership move)

This slice **deliberately replaces** (Spec 338 §"drop-in bar" exception) the three
`memory.update({"state": …})` sites so `move` owns the column:

- `gate/_main.py:55` (`gate.check`) — the `input-required` set becomes
  `ctx.call("lifecycle", "move", lifecycle_id=…, to_state="input-required")`.
- `_substrate_tools.py:89` (`lifecycle_gate`) — same.
- `reflect/_main.py` archives the *session status*, not `Lifecycle.state` — left
  as-is (it writes `status`, a different column; documented as out of scope).

In 339 `move` still accepts any valid-enum transition (the table guard is 340), so
this is behaviour-preserving: the same states get written, now through one verb
that 340 will harden in place.

### Ontology (`ontology.py`)

Reuses the core `Lifecycle` node (`ontology.py:26` — `state · phase`) and adds two
OPTIONAL props via the extension: `kind` (task | session | gate | dispatch …) and
`parameterization` (the 342 seam — default `""`). No new node types in 339; the
transition table (340) and parameterization registry (342) add theirs. The
`lifecycle-management` skill slot is declared (populated by 343).

### What this slice does NOT do

- No transition-table enforcement (340) — `move` only checks enum + no-op.
- No observe verbs (341) and no parameterization variants (342).
- No new typed table — `TypedLifecycleState` (Spec 329) mirrors the graph write
  for free.

## Acceptance (Gherkin)

```gherkin
Scenario: open mints a serving Lifecycle in submitted
  Given a confirmed intent
  When I call lifecycle.open(intent_id, kind="task")
  Then a Lifecycle node exists in state "submitted" SERVING that intent

Scenario: move is the sole state writer and rejects a no-op
  Given an open Lifecycle in state "working"
  When I call lifecycle.move(lid, to_state="working")
  Then it returns an error (no-op refused)
  And no other code path writes Lifecycle.state directly

Scenario: close drives to a terminal state through move
  Given an open Lifecycle in state "working"
  When I call lifecycle.close(lid, outcome="completed")
  Then the Lifecycle state is "completed"

Scenario: gate.check routes its pause through lifecycle.move
  Given a Lifecycle serving the current intent
  When a gate fails via gate.check
  Then the Lifecycle reaches "input-required" via lifecycle.move (not a raw update)
```

## Followup — Implementation Status (2026-06-20)

Not started — scaffold slice drafted. Lands the folder, the `open · move · close`
frame, and the ownership move (three unguarded writes routed through `move`). 340
hardens `move` with the transition table in place.
