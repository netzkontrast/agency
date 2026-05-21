---
slug: spec-workflow-base
type: spec
status: ready
summary: The runner — entry verbs (scaffold/start/resume), Phase graph nodes, Continuation nodes, gate evaluation, and the TTL sweep. Workflows are graph paths; aspects materialize lazily; no state files on disk.
---

> Amended by the capability/aspect/lazy-domaining model — see VOCABULARY.md.

# 05 — Workflow base (the runner)

The runner lives in `workflow/_runner/`. A workflow is a path through the
context graph; the runner walks it, evaluating gates and persisting yields as
graph nodes. A capability's workflow aspect is exactly this path — materialized
lazily (as `Phase` nodes) or authored as phase files.

## Entry verbs

```python
scaffold(domain: str, capability: str, inputs: dict) -> ToolResult
    # author ONE aspect at <domain>/<capability>/ from the domain's aspect-shape template

start(capability: str, phase_id: str, inputs: dict, lazy_link: bool = False) -> PhaseStateEnvelope
resume(session_id: str, phase_id: str, user_response: dict)                  -> PhaseStateEnvelope
```

`scaffold` authors a single aspect in a single domain — there is no eager
cross-domain scaffolding. By default a capability's workflow aspect stays lazy
(materialized as graph nodes) rather than scaffolded.

## Phase nodes

Phases are graph nodes, not manifest arrays:

```
id: phase/<capability>/<phase_id>
payload: { capability, phase_id, body_ref: "phases/<NN>-*.md", lazy_created: false }
```

`start` resolves the `Phase` node, runs its body/handler, evaluates blocking
gates ([03](03-gate.md)), and returns a `PhaseStateEnvelope`.

## Lazy link

```toml
[workflow.lazy_link]
enabled = false   # default: block on unknown phases; opt in to auto-create them
```

When enabled, the runner auto-creates missing `Phase` nodes as it walks — this
is how a capability's workflow aspect materializes lazily, with no authored
folder.

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
