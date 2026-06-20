# Intent · Lifecycle · Gate — three of the four concepts

<!-- doc-source: agency/intent.py agency/lifecycle.py agency/capabilities/gate/_main.py -->
<!-- doc-hash: 7965841abc814702 -->

## Intent (`agency/intent.py`)

The human-owned root. `why` and `what` are merged — a deliverable held with a purpose.

- **`capture(purpose, deliverable, acceptance)`** → records an `Intent` node (unconfirmed).
- **`confirm(intent_id, require_clarity=False, …)`** → labels it a confirmed `Intent`
  (verbs require this). Records the `clarity_score` (Spec 322) on every confirm, and —
  Spec 328 — an **Intent-owned clarity `Gate`** (`kind="clarity"`, the score + verdict)
  linked `GATES`→Intent, so "is this intent fulfilled?" has a typed home + a history of
  checks. Best-effort: a provenance write never fails confirm.
- **`capture_and_confirm(...)`** → the one-shot bootstrap used by `intent_bootstrap` and
  the `agency intent` CLI side-pipe.

Every verb call `SERVES` an Intent; `Registry.invoke` rejects calls whose `intent_id`
is not a confirmed Intent node. The **`intent` capability** ([../../guide/capabilities.md])
adds critical-thinking *methods* over the goal (decompose, premortem, …) — distinct from
this core class, which owns capture/confirm.

## Lifecycle (`agency/lifecycle.py`)

A task/agent state machine: `open · move · close` — the **Lifecycle PILLAR
substrate** (peer to `intent.py`/`memory.py`), reached three isomorphic ways:
`engine.lifecycle.*`, `ctx.lifecycle.*` (the member-capability delegator), and
the `lifecycle_open`/`lifecycle_move`/`lifecycle_close` substrate-tools (the wire
surface, Spec 339).

- **`open(intent_id, *, kind="task", agent="", parameterization="")`** → records a
  `Lifecycle` (state `submitted`, phase 0) that `SERVES` the intent. `kind` and
  `parameterization` (the agent-as-Lifecycle seam, e.g. `"remote-async"`) are
  optional props recorded only when set. Returns the lifecycle id.
- **`move(lc_id, to_state)`** is the **sole** state-shaped writer — it validates
  `to_state` against the closed enum, refuses a no-op, and **enforces the A2A
  transition table** (Spec 340): the legal edges live as data in
  `agency/_lifecycle_data/transitions.json` (overridable by an
  `Artefact{kind:"transition-table"}` graph node, monotone + terminal-floor checked
  via `extend_table`), and an illegal edge (`completed→working`,
  `submitted→completed`) raises a typed `IllegalTransition{from_state, to_state,
  allowed}`. Each accepted transition **emits** (Spec 344):
  terminal/blocked states (`completed·failed·canceled·input-required·auth-required`)
  become a durable graph `Event{name:"lifecycle_transition"}` (`OBSERVED_DURING` the
  intent + lifecycle, reusing the Spec 076 node); every transition also fans a
  `MonitorEvent{source:"lifecycle", kind:"transition"}` onto the Spec 021 channel.
  Intermediate churn (`submitted→working`) stays on the monitor only (panel B4 —
  the graph keeps the Spec 336 low-bloat win). Because emission lives in the sole
  writer, every routed writer emits for free.
- **`close(lc_id, outcome="completed")`** drives to a terminal state through `move`.
- `delegate.fan_out` opens one child Lifecycle per dispatched item via
  `ctx.lifecycle.open(parameterization="remote-async")` (Spec 339), then `move`s it
  to `working` at dispatch.

## Gate (the `gate` capability)

The machine-vs-human split the canon draws (CORE.md:57-62):

- **`gate.check(lifecycle_id, name, passed, evidence)`** — a **machine-checkable**
  predicate. The caller computes `passed`; on `False` it records a `Gate` `BLOCKED_ON`
  edge and flips the Lifecycle to `input-required` **through `lifecycle.move`** (Spec
  339/344 — so the blocked transition emits a durable transition Event for free;
  guarded against a no-op re-reject); on `True`, a `PASSED` edge. It validates the
  lifecycle serves the intent (walking the `SUPERSEDED_BY` chain). Returns the wire
  envelope `{"result": {passed, gate}}`.
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
