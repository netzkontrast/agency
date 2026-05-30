---
slug: spec-intent
type: spec
status: ready
summary: Intent — the human-owned root. A supersedable node carrying purpose + acceptance, with the deliverable as an attribute (why/what merged). capture → confirm → amend (amend via bi-temporal supersede). Everything edges back via SERVES. Proven: capture/confirm/amend and as-of reconstruction.
---

# Intent

> **Status: specced; proven where noted.** Intent is the human's root, not a
> concept the engine executes on its own — the engine executes Capability /
> Lifecycle / Memory in service of it.

## Concept

The human owns the goal. Intent is a **supersedable node** carrying **purpose +
acceptance**, with the **deliverable as an attribute**. why and what are NOT two
domains: a deliverable change with the purpose held is just an attribute change
on one Intent (the panel's finding). Intent is the root every action edges back
to.

## Interface

```
capture(purpose, deliverable, acceptance) -> Intent node (status: draft)
confirm(intent_id)                         -> intent_id (status: confirmed, in place)
amend(intent_id, **changes)                -> new version (bi-temporal supersede)
```

- `capture` records a draft Intent.
- `confirm` flips it to `confirmed` **in place** — confirming does not fork
  identity, so `SERVES` edges stay stable.
- `amend` is a bi-temporal **supersede**: the *what* changes while the *why*
  holds, and the prior version keeps its valid window for `as_of` reconstruction.

**Proven:** `Intent.capture/confirm/amend`; after `amend(deliverable=...)`,
`recall(intent, as_of=before)` still returns the old deliverable while the new
version carries the new deliverable and the unchanged purpose.

## Intent node

```
label: Intent
fields: purpose, deliverable, acceptance, status   (+ bi-temporal vfrom/vto)
```

## Interactions

- Every action node (Invocation, Lifecycle, Artefact, Gate, …) carries a
  **`SERVES → Intent`** edge.
- The Intent node lives in Memory but is conceptually upstream of execution
  history: it is the goal, not a record of the run.
- A gate that needs a human decision pauses the Lifecycle at `input-required` →
  Intent re-entry (clarify / approve / `amend`).
