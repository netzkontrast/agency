# Memory — the bi-temporal graph store

<!-- doc-source: agency/memory.py -->
<!-- doc-hash: 10e0240411b23877 -->

`agency/memory.py` wraps a **GraphQLite** graph as the engine's single store. Files are
a rendered view; the graph is the source of truth.

## Surface

- **`record(label, props, node_id=None)`** → create (or upsert, when `node_id` is given)
  a node; enforces the effective ontology. Returns the node id.
- **`link(src, dst, REL)`** → create a typed edge.
- **`update(node_id, props)`** → patch a node (e.g. flip a `Lifecycle` to
  `input-required`).
- **`recall(node_id, as_of=None)`** → fetch one node (bi-temporal: `as_of` reads the
  graph at a past logical tick).
- **`find(label, as_of=None)`** → all current nodes of a label.
- **`provenance(intent_id)`** → the cross-concern audit for one intent (walks `SERVES`,
  `PRODUCES`, `OBSERVED_DURING`, … and the `SUPERSEDED_BY` chain via `_intent_chain`).
- **`g.query(cypher, params)`** → raw graph query (used by gates, provenance).

## Bi-temporal

Every write is stamped with a logical tick; nothing is destroyed. `recall(id, as_of=t)`
reads history; `SUPERSEDED_BY` chains let an amended `Intent` keep its provenance (the
`gate.check` guard walks the whole chain so a gate against an amended intent still
resolves). This is what makes a release/decision audit reproducible.

## Reading the graph

Two query surfaces an agent uses:

- **`analyze.graph`** (Spec 084) — a census of node labels + a typed listing; the
  general "read the graph" surface in code-mode.
- **`memory_graph_provenance(intent_id)`** — the bootstrap tool that drills one intent's
  full provenance in a single traversal.

## The provenance moat

Because `Registry.invoke` records an `Invocation SERVES Intent` for *every* verb, and
`act`/`effect` verbs add `PRODUCES`/gate edges, any question of the form "show me every
X for this goal" is one traversal. The `music` example exists to demonstrate exactly
this (a release audit) — something a flat handler library structurally cannot do.

## The typed projection (Spec 289 + 326–330)

The graph stays write-authoritative, but every write is also MIRRORED one-way into
typed SQLModel rows sharing the graph's one SQLite connection (`memory.entities`,
an `EntityStore`). Spec 289 mirrors any node into a generic `EntityRecord` JSON
blob; Spec 326–330 add an **explicit relational layer** for the four-concept core
— `TypedIntent` · `TypedInvocation` · `TypedAgent` · `TypedGate` ·
`TypedAcceptanceCriterion` · `TypedLifecycleState` · `TypedArtefact` plus a general
`TypedEdge` spine — with real **foreign-key columns** (`serves_intent_id` ·
`agent_id` · `parent_intent_id` · `intent_id` · `produced_by_id`) set from the
edges as they land (`SERVES`/`PERFORMED_BY`/`PARENT_INTENT`/`VALIDATES`/`GATES`/
`PRODUCES`). So the interweave (Capability · Lifecycle · Memory → Intent) is a
typed SQL **join**, not just a Cypher traversal. `memory.intents` (an
`IntentStore`) is the typed-join read API — `serves` · `intent_tree` ·
`provenance` · `fulfilment` — guarded by a parity test against the graph. The
mirror is failure-isolated (a projection error never fails the graph write), and
`supersede` carries the prior version's FK columns forward so a superseded node
stays in the typed joins.

## Related

- The schema of what's stored: [ontology.md](ontology.md).
- Who writes it: [capability-system.md](capability-system.md).
