---
slug: spec-workflow-base
type: spec
status: ready
summary: The runner — entry verbs (scaffold/start/resume), Phase graph nodes, Continuation nodes, gate evaluation, and the TTL sweep. Workflows are graph paths; no state files on disk.
---

# 05 — Workflow base (the runner)

The runner lives in `workflow/_runner/`. A workflow is a path through the
context graph; the runner walks it, evaluating gates and persisting yields as
graph nodes.

## Entry verbs

```python
scaffold(domain: str, row: str, inputs: dict) -> ToolResult
    # create ONE row at <domain>/<row>/ from the domain's row-shape template

start(row: str, phase_id: str, inputs: dict, lazy_link: bool = False) -> PhaseStateEnvelope
resume(session_id: str, phase_id: str, user_response: dict)           -> PhaseStateEnvelope
```

`scaffold` adds a single row to a single domain — there is no cross-domain
scaffolding.

## Phase nodes

Phases are graph nodes, not manifest arrays:

```
id: phase/<row>/<phase_id>
payload: { row, phase_id, body_ref: "phases/<NN>-*.md", lazy_created: false }
```

`start` resolves the `Phase` node, runs its body/handler, evaluates blocking
gates ([03](03-gate.md)), and returns a `PhaseStateEnvelope`.

## Lazy link

```toml
[workflow.lazy_link]
enabled = false   # default: block on unknown phases; opt in to auto-create them
```

## Continuation (no files)

A yield (blocked, or awaiting the user) is a node:

```
id: continuation:<session_id>:<phase_id>
payload: { session_id, phase_id, opaque_state, envelope, created_at_epoch }
```

`resume` hydrates the node, merges the user response, and re-walks. There is no
`_state/` directory.

## Boot

`pipeline.boot()` is idempotent and sweeps `Continuation` nodes older than 30
days (compared via `created_at_epoch`).
