---
slug: spec-where
type: spec
status: ready
summary: where — memory. A bi-temporal, append-only GraphQLite graph plus artefacts. record/link/supersede (lifecycle) + recall/find/validate (observe). Reads go through where.project(): ranked, token-budgeted, TOON-encoded deltas — never raw history. Artefact drivers move bytes to user storage.
---

# where — memory

> **Status: specced — not built.** The `jules` where aspect (sessions /
> patches / lessons) is LAZY — it materializes as `Artefact` / memory nodes the
> moment jules first produces or learns. `where` is the only persistent state.

## Concept

`where` is memory: a single **bi-temporal, append-only** GraphQLite graph
(SQLite + Cypher + node/edge primitives + graph algorithms) plus artefacts. It
is the only persistent state. Facts are **never overwritten** — a corrected
fact `supersede`s the prior one, leaving a complete audit trail (valid-time and
transaction-time).

## Interface — the canonical frame

| Role | Verb | Meaning |
|---|---|---|
| open | `record` | append a node (a fact, an Artefact) |
| move | `link` | append an edge between nodes |
| close | `supersede` | mark a node superseded by a newer one (never delete/overwrite) |
| read | `recall` | read memory — **always via `where.project()`** |
| find | `find` | search the graph — **always via `where.project()`** |
| check | `validate` | check a node/edge against its schema |

## where.project() — the only read path

`recall` and `find` go through **`where.project()`**: a **ranked,
token-budgeted, TOON-encoded** projection that returns **DELTAS, never raw
history**. This is how an append-only store coexists with compaction — the full
history stays on disk; what the model ever sees is a budgeted projection. Code-
mode (see [engine](engine.md)) calls `where.project()` and filters/joins
in-sandbox.

## Nodes & edges

Typed nodes include `Intent`, `Session`, `Task`, `Gate`, `Artefact`,
`Dispatch`, `SharedContext`, `Slot`, `Capability`. Typed edges include
`SERVES_INTENT`, `DRIVES`, `PRECEDES`, `PRODUCES`, `DERIVED_FROM`, `SUPERSEDES`.

## Artefact node + drivers

```
label: Artefact
fields: content_type, sha256, size_bytes, created_at, produced_by, derived_from,
        artefact_driver, driver_pointer, capability
```

The graph holds the **record**; an **artefact driver** moves the **bytes** to
user storage (`fs` mandatory; `repo` / `s3` / `http` / `drive` follow). No
metadata sidecar files are ever written to user storage — these are graph
properties.

## Interactions

- Every other domain records here: `who` writes Sessions/Dispatch, `when`
  writes Tasks/gate results, `how` outputs become Artefacts, `intent` pins the
  Intent node.
- Append-only + `supersede` + `where.project()` together satisfy the
  context-engineering commitments in ARCHITECTURE.md.
