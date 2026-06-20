---
spec_id: "339"
slug: lifecycle-substrate-write-frame
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 3, 4]
depends_on: ["016", "024", "080", "290", "338"]
domain: lifecycle
wave: program-master
parent_spec: "338"
---

# Spec 339 — Harden the Lifecycle **substrate** + the write frame (`open · move · close`)

> Child of the Lifecycle-pillar deep program (Spec 338). The **foundation
> slice** — and, per the owner directive *"lifecycle isn't a capability — it's its
> own pillar"*, it hardens the **substrate** `agency/lifecycle.py` (peer to
> `intent.py`/`memory.py`), NOT a `lifecycle` capability folder. It lands the
> canonical *write* frame (`open · move · close`) as substrate methods reached via
> `ctx.lifecycle` + `lifecycle_*` wire tools, and makes `move` the **sole writer**
> of `Lifecycle.state`. The transition table (340), events (344), and
> parameterization (342) are pure additions onto this hardened substrate.

## Why

Spec 338 §Architecture calls for a `lifecycle` capability that owns the
CORE.md §3 verb frame. The codegraph deep-analysis (Spec 338 §Why) found the
problem is not "nothing" but **three divergent, hand-rolled minting paths** plus
unguarded state writes:

- `agency/lifecycle.py` — a non-capability `Lifecycle` class (`open · move ·
  complete · status`) with bugs vs. the canon: `open()` starts at `working` (not
  `submitted`); `move(lc_id, gate, ok)` is **gate-shaped**, not state-shaped; no
  `auth-required`. Used by only `engine.py` + `music/drivers_production.py`.
- `delegate.fan_out` (`delegate/_main.py:488`) **hand-rolls** the node:
  `record_and_serve("Lifecycle", {state:"working"})` — bypassing that class.
- `develop.session_start` mints a **separate** `SessionLifecycle{mode,status}`.
- `state` is then written by unguarded `memory.update` from `gate.check`, the
  `lifecycle_gate` substrate tool, `Lifecycle.move/complete`, and `delegate`.

So this slice is **promote + unify**, not create-from-scratch: lift the substrate
`Lifecycle` class into a first-class capability, fix `open`→`submitted`, split the
gate-shaped `move` into a general state-shaped `move`, and make that `move` the
**single chokepoint** every state change flows through. After it, the three
minting paths call `lifecycle.open` and nothing outside `lifecycle.move` writes
`state` (N1, N2, N6 from Spec 338). Enforcement (the transition table) is 340;
this slice is complete on **ownership**.

## Design — harden the substrate (not a capability folder)

### Where the code lives (pillar substrate, peer to `intent.py`/`memory.py`)

```
agency/lifecycle.py            # HARDEN IN PLACE — class Lifecycle (engine.lifecycle)
                               #   open · move · close (state machine); _assert_transition (stub → 340)
agency/_lifecycle_data/        # transitions.json (340) · parameterizations.json (342) — definable registries
agency/capability.py           # CapabilityContext gains `ctx.lifecycle` → delegator to engine.lifecycle
agency/_substrate_tools.py     # + LifecycleOpen/Move/Close SubstrateTool (wire surface; take intent_id
                               #   explicitly, like intent_bootstrap — they SERVE, requires_intent as needed)
```

There is **no** `agency/capabilities/lifecycle/` and **no** `CapabilityBase`
subclass. The frame is substrate, surfaced three isomorphic ways (CORE.md
harness-in-harness): the `Lifecycle` method, `ctx.lifecycle.*` for member caps,
and the `lifecycle_*` substrate-tools for the wire/CLI. This is exactly how Intent
(`intent.py` + `intent_bootstrap`) and Memory (`memory.py` + `ctx.memory` +
`memory_graph_provenance`) are shaped.

### The write frame (hardened `agency/lifecycle.py`)

The current class (`open→working`, gate-shaped `move`, `complete`, `status`) is
fixed to the canon:

```python
class Lifecycle:                       # engine.lifecycle — the pillar substrate
    def open(self, intent_id, *, kind="task", agent="", parameterization="") -> str:
        # FIX (was `working`): mint in `submitted` per CORE.md; SERVES the intent;
        # optional agent → DISPATCHED_TO (the parameterization seam, 342).
        ...

    def move(self, lc_id, to_state, *, evidence="") -> str:
        # SPLIT (was gate-shaped `move(lc, gate, ok)`): a general STATE transition.
        # The SOLE writer of Lifecycle.state. 339: validate value + refuse no-op;
        # 340: full transition-table guard; 344: emit a LifecycleEvent.
        ...

    def close(self, lc_id, *, outcome="completed", evidence="") -> str:
        # Terminal move; records a Spec 328 `completion` Gate keyed to the intent
        # (panel W-2) reading its AcceptanceCriteria. Not a parallel writer.
        ...
```

`ctx.lifecycle` delegates to this instance; the `lifecycle_open/move/close`
substrate-tools wrap it for the wire. `open` REUSES the
`_invoke.InvocationRecorder.open` agent-upsert pattern (rule 2 — one way to mint a
performer).

> **Migration of the three minting paths (panel G-1 / S-1).** `codegraph impact`
> on `Lifecycle` (2 callers: `engine.py`, `music/drivers_production.py`) +
> `SessionLifecycle` (readers: `develop.session_check`/`session_resume`,
> `reflect.synthesize_session`) bounds the blast radius:
> - `delegate.fan_out`'s `record_and_serve("Lifecycle", {state:"working"})` →
>   `ctx.lifecycle.open(parameterization="remote-async")` (342).
> - `subagent.develop:66`'s `ctx.memory.update(child, {"state":"completed"})` →
>   `ctx.lifecycle.move(child, "completed")` (its "verified join" comment becomes
>   true once 342 wires verify).
> - `SessionLifecycle` becomes `Lifecycle{parameterization="session"}` carrying
>   `mode`/`status` as parameterization-scoped props (the `session` parameterization,
>   342; `develop`/`reflect` readers re-point). **Legacy nodes** read
>   `parameterization=""→"default"`; `open→submitted` affects only NEW lifecycles,
>   so `manage`'s `active_states={submitted,working}` already covers both.

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
