---
slug: spec-who
type: spec
status: ready
summary: who — the agent-SESSION lifecycle. dispatch/handoff/release (lifecycle) + poll/roster/verify (observe), the orchestration verbs (retry/respawn/escalate/fan_out/reclaim_slot), and the Dispatch / SharedContext / Slot nodes. Dispatcher is who.<actor>; the role is a parameter. DRIVES links a session to its when-task.
---

# who — the agent-session lifecycle

> **Status: specced — not built (except where noted).** The `jules` who aspect
> is the MINIMAL committed proof — one authored aspect; the rest of `who` is
> specced.

## Concept

`who` owns the **agent-SESSION** lifecycle: which actor performs the work, and
its dispatch / handoff / supervision. It is a **closed** domain — every verb
maps to the canonical two-axis frame. It does NOT own the task; that is `when`.

## Interface — the canonical frame

| Role | Verb | Meaning |
|---|---|---|
| open | `dispatch` | create a Session for an actor to perform work |
| move | `handoff` | pass work to another actor (new nested session) |
| close | `release` | end a session |
| read | `poll` | read a session's live status |
| find | `roster` | list sessions / available actors |
| check | `verify` | confirm a session's claimed result (e.g. branch on remote) |

## Dispatcher vs dispatchee

`who.<actor>.dispatch(role=jules, intent=I)` — **`who.<actor>` is the
DISPATCHER**; the target **role is a PARAMETER** (the dispatchee). A
who-capability is the orchestrator; the role it spawns is data, not a separate
domain.

## Orchestration verbs (beyond the frame)

| Verb | Rule |
|---|---|
| `retry` | probe a stalled session with one focused message |
| `respawn` | re-create a session — **canon guard: NEVER respawn jules if a patch already exists; DO if the patch is empty** |
| `escalate` | raise to a supervisor / human |
| `fan_out` | dispatch many sessions in parallel (guarded as a critical section) |
| `reclaim_slot` | return a `Slot` to the pool |

## Nodes (in `where`)

- **Session** — one actor's run.
- **Dispatch** — a per-hop correlation node; nesting them enables
  **harness-in-harness** (a dispatchee that itself dispatches).
- **SharedContext** — attached on `handoff` so the receiving session inherits
  CONTEXT, not just a baton.
- **`Slot`** — concurrency/quota accounting (an engine guard `who` reads).

## Interactions

- A **`DRIVES`** edge links a Session to the **when**-task it advances — the
  who ↔ when boundary. State is never duplicated across the two.
- `poll` returning `COMPLETED` is NOT success; always `verify` (silent-fail
  lesson — see LESSONS.md).
- Sessions and dispatch hops are recorded in `where` (append-only).
