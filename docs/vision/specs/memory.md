---
slug: spec-memory
type: spec
status: ready
summary: Memory — the moat. One bi-temporal, append-only GraphQLite graph holding every node and edge. record·link·supersede (write) + recall·find·validate (read). project(query, budget) returns ranked, token-budgeted, as-of deltas. Cross-concern provenance is a single traversal. Seed-proven: bi-temporal supersede, project, one-traversal provenance.
---

# Memory

> **Status: specced; seed-proven where noted.** The seed runs Memory on real
> GraphQLite (SQLite + Cypher) and answers the provenance query in one traversal.

## Concept

`Memory` is the moat: a single **bi-temporal, append-only** GraphQLite graph
holding **every** node — Intent, Capability invocations, Lifecycle states,
agents, artefacts, gates — and their edges. Facts are **never overwritten** — a
corrected fact `supersede`s the prior one, which keeps its valid window
(valid-time and transaction-time). It is the only persistent state.

## Interface

```
# write
record(label, props)        -> node id (append-only; vfrom/vto bi-temporal window)
link(src, dst, rel, props?) -> edge
supersede(node_id, changes) -> new version id (old version's window closes; SUPERSEDED_BY edge)

# read
recall(node_id, as_of?)     -> props (as-of-aware)
find(label, as_of?)         -> current (or as-of) nodes of a label
validate(node_id, predicate)-> bool
project(query, budget, as_of?) -> ranked, token-budgeted deltas (never raw history)

# the moat
provenance(intent_id)       -> one traversal: serves + agents + artefacts + gates
```

**Seed-proven:** bi-temporal `supersede` (the *what* changes while the *why*
holds, reconstructable `as_of`); `project` (recency-ranked, budget-capped);
`provenance` (one Cypher walk).

## project(query, budget) — the only read path

`recall` / `find` over large history go through **`project`**: a ranked,
token-budgeted, supersession-aware (`as_of`) projection returning **DELTAS, never
raw history**. This is how an append-only store coexists with compaction — the
full history stays on disk; what the model sees is always a budgeted projection
(production: BM25 + semantic + graph BFS → RRF/MMR/recency blend → token-greedy
cut → TOON-or-JSON).

## Nodes & edges

Typed nodes: `Intent`, `Invocation`, `Lifecycle`, `Agent`, `Artefact`, `Gate`,
`Capability`. Typed edges: `SERVES`, `PRODUCES`, `PERFORMED_BY`, `DISPATCHED_TO`,
`PRECEDES`, `SUPERSEDED_BY`, `PASSED`.

## The moat — cross-concern provenance in one traversal

```
provenance(I) = {
  serves:    every action that SERVES I,
  agents:    the Agent that PERFORMED_BY each action,
  artefacts: the Artefact each action PRODUCES,
  gates:     the Gate the Lifecycle PASSED,
}
```

**The one thing a flat SDK + memory-tool rival cannot match:** this is a *single
graph traversal* from the Intent, not a join across four systems. **Seed-proven**
end to end.

## Artefact node + drivers

The graph holds the **record**; an **artefact driver** moves the **bytes** to
user storage (`fs` mandatory; `repo` / `s3` / `http` / `drive` follow). No
metadata sidecar files are written to user storage — these are graph properties.
(This collapses the prototype's dual-store drift: `rebuild_state`, `db_*` tweet
SQLite, and path-resolution helpers exist only because content lived on disk
beside a cache; with one graph there is nothing to re-sync.)

## Interactions

- Every concept records here: Capability writes Invocations/Artefacts, Lifecycle
  writes states/gates, Intent records the root.
- Append-only + `supersede` + `project` together satisfy the
  context-engineering commitments in ARCHITECTURE.md.
