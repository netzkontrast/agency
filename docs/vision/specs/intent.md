---
slug: spec-intent
type: spec
status: ready
summary: Intent (why/what) — the human's root. why.capture/why.confirm produce a single Intent node, pinned once and referenced by node-id (cache-safe). Every action edges back via SERVES_INTENT. Intent is its own root, distinct from where's execution memory.
---

# Intent (why / what)

> **Status: specced — not built.** Intent is the human's root, not a domain
> the engine executes. The engine executes who/how/when/where in service of it.

## Concept

The human owns **Why / What** — the reason the work exists and what "done"
means. This is captured once and persisted as a single **Intent node**, then
referenced by id forever after. Intent is its **own root**, distinct from
`where`'s execution memory: `where` remembers what happened; the Intent node
remembers why it was supposed to.

## Interface

```
why.capture(text)        -> draft intent (proposed What/Why, success criteria)
why.confirm(draft, ...)  -> Intent node (pinned once)
```

- `why.capture` proposes a structured intent from the human's words.
- `why.confirm` freezes it into an **Intent node** in `where` and **pins it
  once**. After pinning, the intent is referenced by **node-id** only — its
  text is never re-pasted into context (cache-safe; preserves KV-cache
  prefixes).

## Intent node

```
label: Intent
fields: what, why, success_criteria, status, pinned_at
```

## Interactions

- Every action node (Session, Task, Artefact, …) carries a
  **`SERVES_INTENT → I`** edge to its root intent.
- `who.dispatch(intent=I)` and `when.start(...)` take the intent **by id**.
- The Intent node lives in `where` but is conceptually upstream of execution
  memory: it is the goal, not a record of the run.
