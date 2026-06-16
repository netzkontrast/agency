# Ontology — the graph schema

<!-- doc-source: agency/ontology.py -->
<!-- doc-hash: 72060e5e13ad578a -->

`agency/ontology.py` defines the node/edge/enum backbone every capability's data is
built on, and how a capability *extends* it.

## The core schema

`NODE_SCHEMAS` is the closed set of core node labels, each with its required fields:

- **`Intent`** `[purpose, deliverable, acceptance]` — the human root.
- **`Invocation`** `[capability, verb, role]` — every verb call.
- **`Reflection`** `[scope, text]` — notes/observations recorded via `reflect`.
- **`Lifecycle`** `[state, phase]` · **`Gate`** `[name, passed, evidence]` · **`Agent`**.
- **`Artefact`** `[kind]` — a produced document/file/published-skill.
- **`Skill`** `[name, kind]` · **`Phase`** `[skill, index, name, produces]` — populated
  by `skills.index` (Spec 026).
- **`Event`** — unified hook events (Spec 076).

Edges (`EDGE_TYPES`) include `SERVES`, `PRODUCES`, `OBSERVED_DURING`, `HAS_PHASE`,
`PASSED`/`BLOCKED_ON`, `SUPERSEDED_BY`, `PERFORMED_BY`, `PRECEDES`/`NEXT`, … The core
ships **no domain skills** — those are owned by the capabilities that add them.

## `OntologyExtension` — how a capability extends the schema

A capability declares one `OntologyExtension`:

```python
OntologyExtension(
    nodes={"Album": ["artist", "title", "type"]},     # new node labels + fields
    enums={("Album", "type"): {"documentary", ...}},  # closed value sets on a field
    skills={"album-concept": {...}},                  # walkable phase-graph schemas
    schemas={"album-concept": ["artist", "title"]},   # artefact-kind required fields
)
```

At bootstrap the engine merges each extension **strictly** onto core (`Ontology.extend`
/ the enforcer): a node-label or skill-name collision raises, so two capabilities can
never silently redefine the same type. Enums are closed value sets enforced on write.

## Why strict

The graph is the store; strict merge is what lets the engine trust the data without a
schema migration step. A capability that wants a new field on `Album` declares the full
field list in its extension; the merge validates compatibility. This is the substrate
that makes the [drop-in bar](../../guide/extending.md) safe.

## Related

- Who writes these nodes: [capability-system.md](capability-system.md) (`ctx.record`).
- Where they live + how they're queried: [memory.md](memory.md).
- Skill/Phase promotion into the graph: [skills.md](skills.md).
