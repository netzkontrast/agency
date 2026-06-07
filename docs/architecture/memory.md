# Memory — the bi-temporal graph store

<!-- doc-source: agency/memory.py -->
<!-- doc-hash: ce9d8d48febaf6c2 -->

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

## Related

- The schema of what's stored: [ontology.md](ontology.md).
- Who writes it: [capability-system.md](capability-system.md).
