---
slug: spec-when
type: spec
status: ready
summary: when — the TASK/process lifecycle. start/advance/complete (lifecycle) + status/list/check (observe), where check is the gate. Gates guard phase transitions. A DRIVES edge links a who-session to the when-task it advances; state is never duplicated across who and when.
---

# when — the task / process lifecycle

> **Status: specced — not built.** The `jules` when aspect (its task state
> machine, incl. silent-fail recovery) is LAZY — it materializes as `Task` /
> gate nodes when first needed.

## Concept

`when` owns the **TASK / process** lifecycle: order, gates, scheduling,
triggers. It is a **closed** domain — every verb maps to the canonical frame. It
does NOT own the actor; that is `who`.

## Interface — the canonical frame

| Role | Verb | Meaning |
|---|---|---|
| open | `start` | begin a task (its phases + gates) |
| move | `advance` | move the task to the next phase |
| close | `complete` | finish the task |
| read | `status` | read a task's current phase/state |
| find | `list` | list tasks |
| check | `check` (gate) | evaluate a gate guarding a transition |

## Tasks, phases, gates

- A **Task** node owns an ordered set of phases (e.g.
  `investigate → patch → verify → pr`).
- A **gate** guards a transition; `check` evaluates it. A gate is
  **hard-blocking** (must pass to `advance`) or **advisory** (surfaced as a
  warning, never blocks). Example: a `tests-green` hard gate before `pr`.
- Phases and gates materialize lazily as graph nodes (the default) or may be
  authored when a capability has fixed structure.

## who ↔ when boundary (DRIVES)

`when` owns the task; `who` owns the session. A **`DRIVES`** edge links a
who-session to the when-task it advances. **State is never duplicated**: phase /
gate state lives in `when`; session state lives in `who`; the `DRIVES` edge is
the join.

## Interactions

- `who.dispatch` opens a session; `where.link(session, task, rel="DRIVES")`
  joins it to the task `when.start` opened.
- Task transitions and gate results are recorded in `where` (append-only).
- A passing hard gate is the precondition the engine enforces before `advance`.
