---
slug: spec-lifecycle
type: spec
status: ready
summary: Lifecycle — the task/agent state-machine. Write frame open·move·close + observe frame read·find·check·watch. States align with A2A tasks (submitted·working·input-required·completed·failed·canceled). An agent is a Lifecycle parameterization (a remote async agent inserts verify; COMPLETED != done). Gates = input-required -> Intent re-entry. Proven.
---

# Lifecycle

> **Status: specced; proven where noted.** The engine runs an agent Lifecycle
> (open → gate → complete) and encodes `COMPLETED ≠ done`.

## Concept

`Lifecycle` is the task/agent state-machine. It owns *state + gates* for a unit
of work. Two verb axes:

- **write:** `open · move · close`
- **observe:** `read · find · check · watch` (`check` validates against rules;
  `watch` is a continuous monitor — distinct operations).

## States (A2A-aligned)

```
submitted · working · input-required · completed · failed · canceled
```

States mirror the A2A task model. **`COMPLETED ≠ done`** — a state of
`completed` means "idle, awaiting input," not "work done and pushed."

## Interface (seed shape)

```
open(intent_id, agent=None) -> Lifecycle node (state: working)   # SERVES intent; DISPATCHED_TO agent
move(lc_id, gate, ok)       -> "working" (records a PASSED Gate) | "input-required" (human re-entry)
close / complete(lc_id)     -> "completed"
read / status(lc_id)        -> current state
```

**Proven:** `open(intent, agent="jules")` creates a Lifecycle that `SERVES`
the Intent and is `DISPATCHED_TO` an Agent node; `move(gate, ok=True)` records a
`PASSED` Gate and advances; `complete` reaches `completed`.

## An agent is a Lifecycle parameterization

The old "who" is not a separate concept. An **agent-session is a Lifecycle whose
transitions/observers differ**: a remote async agent inserts a `verify` step
because `COMPLETED ≠ done`; a local subagent skips it. A fan-out of N parallel
agents is N Lifecycles under one Intent.

**Proven:** the `jules` capability returns `status: COMPLETED` with
`branch_pushed=False`; the inserted `verify` step returns `done=False` until a
real branch exists — the silent-fail lesson as a first-class observe-step.

## Gates = input-required → Intent re-entry

A gate is a Lifecycle step that pauses at `input-required`. A gate needing a
human is an **`elicit`** step (see [skills-and-gates.md](skills-and-gates.md)):
the prompt streams out, the answer resumes the Lifecycle, and the outcome is
recorded as a `Gate` node (`PASSED` or blocked). A hard gate must pass to
`move`; an advisory gate surfaces a warning and never blocks.

## Interactions

- A Lifecycle `SERVES` an Intent; its transitions, gates, and the agents it
  dispatches to are all recorded in Memory (append-only).
- Orchestration concerns beyond the frame (`retry` / `respawn` / `escalate` /
  `fan_out` / `reclaim_slot`) ride on the Lifecycle with engine-guard middleware
  (`Slot`/quota). Canon guard: **never `respawn` an agent if a patch already
  exists; do only if the patch is empty.**
