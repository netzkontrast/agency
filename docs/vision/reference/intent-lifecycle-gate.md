# Intent · Lifecycle · Gate — three of the four concepts

<!-- doc-source: agency/intent.py agency/lifecycle.py agency/capabilities/gate/_main.py -->
<!-- doc-hash: 594a3ac8144ca1ee -->

## Intent (`agency/intent.py`)

The human-owned root. `why` and `what` are merged — a deliverable held with a purpose.

- **`capture(purpose, deliverable, acceptance)`** → records an `Intent` node (unconfirmed).
- **`confirm(intent_id)`** → labels it a confirmed `Intent` (verbs require this).
- **`capture_and_confirm(...)`** → the one-shot bootstrap used by `intent_bootstrap` and
  the `agency intent` CLI side-pipe.

Every verb call `SERVES` an Intent; `Registry.invoke` rejects calls whose `intent_id`
is not a confirmed Intent node. The **`intent` capability** ([../../guide/capabilities.md])
adds critical-thinking *methods* over the goal (decompose, premortem, …) — distinct from
this core class, which owns capture/confirm.

## Lifecycle (`agency/lifecycle.py`)

A task/agent state machine: `open · move · close`.

- **`open(intent_id, agent=None)`** → records a `Lifecycle` (state `working`, phase 0)
  that `SERVES` the intent. Returns the lifecycle id.
- The lifecycle advances through phases; a gate can pause it (`input-required`).
- `delegate.fan_out` opens one child Lifecycle per dispatched item.

## Gate (the `gate` capability)

The machine-vs-human split the canon draws (CORE.md:57-62):

- **`gate.check(lifecycle_id, name, passed, evidence)`** — a **machine-checkable**
  predicate. The caller computes `passed`; on `False` it records a `Gate` `BLOCKED_ON`
  edge and flips the Lifecycle to `input-required`; on `True`, a `PASSED` edge. It
  validates the lifecycle serves the intent (walking the `SUPERSEDED_BY` chain). Returns
  the wire envelope `{"result": {passed, gate}}`.
- **`gate.adjudicate(a, b, lifecycle_id="")`** (Spec 303) — adjudicates two CONFLICTING
  concerns by delegating to `doctrine.resolve` (the safety > correctness >
  maintainability > speed hierarchy), recording a `Gate` node + a `doctrine.resolve`
  Invocation that SERVES the intent — doctrine's real consumer.
- **`lifecycle_gate`** (a bootstrap tool / `elicit`) — the **terminal human** "ready /
  ship it?" confirmation (the hard final phase of a gated skill).

A worked example is `music.release_check` → `gate.check` ("all tracks mastered?"), whose
fail pauses the release lifecycle and returns a typed `GATE_FAILED`.

## Related

- The fourth concept: [memory.md](memory.md).
- Gated, walkable skills: [skills.md](skills.md).
