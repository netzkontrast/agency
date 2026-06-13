---
spec: 288
title: sqlmodel-entity-store
status: Implementing (Slice 1 shipped)
depends_on: [048, 286]
clusters: [core, substrate]
vision_goals: [4, 5, 7]
---

<!-- doc-source: agency/memory.py agency/ontology.py agency/_entities.py -->

# Spec 288 — SQLModel typed entities for every graph data object

> User directive (2026-06-13): integrate **SQLModel** for **all data entities**,
> **linked to the graph entities**, in **core dependencies**, **all OOP**.
> Reuse the **established schemas + the graph ontology** as the source of truth;
> create **SQLModel validation code for the graph parts**. Goal: a FastAPI
> frontend later, while holding the graph completely and querying entity
> contents inline.

## Advice — what the current graph implementation makes possible

Checked `agency/memory.py`, `agency/ontology.py`, and the `graphqlite` package:

- **`graphqlite` is a SQLite *extension*** (`graphqlite.so`) loaded onto a
  standard `sqlite3.Connection` (`connection.py`: `connect()` → `sqlite3.connect`
  + `load_extension`). `Memory` holds it at `self.g._conn` (a graphqlite
  `Connection`), whose underlying `sqlite3.Connection` is `.sqlite_connection`
  / `._conn`. Cypher runs as `SELECT cypher(?, ?)`; **`Connection.execute(sql)`
  runs raw SQL on the SAME connection**.
- **Therefore one `.db` file holds both** the graph's extension-managed tables
  AND SQLModel/SQLAlchemy entity tables — no second database, no cross-process
  sync. A SQLAlchemy engine bound to the same path (or the same connection)
  creates the entity tables alongside the graph.
- **Inline entity-content query is feasible**: the graph node carries the entity
  **id** (PK); a raw-SQL JOIN (`Connection.execute`) joins Cypher-returned node
  ids to the entity table in one statement. (Today node props are denormalised
  onto the node, so Cypher `WHERE n.field = …` already filters inline; the SQL
  store makes the full typed row the join target.)
- **The ontology is the schema authority** (`Ontology.nodes` = label→required
  fields, `Ontology.enums` = (label,field)→allowed). `Memory.record` already
  validates via `ontology.violations`. SQLModel models **derive from these**
  (rule 2: derive, don't duplicate) — no hand-authored parallel schema.

## Design (all OOP)

```
Ontology (schema authority: nodes + enums + schemas)
   │  derive (rule 2)
   ▼
EntityModels  ──build──▶  one SQLModel class per label  (Spec 288)
   │                          ├─ Slice 1: table=False → Pydantic VALIDATION
   │                          │           (required-present + enum-membership,
   │                          │            FastAPI-ready typed surface)
   │                          └─ Slice 2: table=True  → canonical SQLite rows
   │                                      in graphqlite's OWN .db (shared conn)
   ▼
Memory.record(label, props)  ── validate via EntityModels ──▶ graph node
   (node.id == entity PK; the graph references the id, holds the edges)
```

- **`EntityModels` (registry, OOP)** — given the effective `Ontology`, lazily
  builds + caches a SQLModel model per node label: required fields from
  `ontology.nodes[label]`, enum fields typed `Literal[...]` from
  `ontology.enums`. `validate(label, props)` runs Pydantic validation and
  returns the same violation-string shape as `ontology.violations` (parity).
- **Link to graph**: the graph node id IS the entity PK (`<label>:<uuid8>`,
  already the convention). Slice 2's `table=True` rows key on that id; the graph
  stores the id + edges; `entity_join(node_ids)` fetches typed rows via raw SQL.
- **FastAPI-ready**: the same SQLModel classes back FastAPI request/response
  models later (Slice 3) — zero re-definition.

## Slices

1. **Validation layer (this slice).** `agency/_entities.py`: `EntityModels`
   derives a SQLModel validation model per label from the ontology; `validate`
   has parity with `ontology.violations`. Behaviour-preserving (additive; not
   yet wired into `Memory`). Tests prove parity on core + extension labels.
2. **Canonical SQLite store + wiring.** `table=True` entity tables in
   graphqlite's `.db` (shared `sqlite_connection`); `Memory.record` writes the
   typed row + the graph node (id link); `entity_join` for inline content query;
   `agency_doctor` reports the entity-store backend.
3. **FastAPI surface.** Read API over the entity tables + provenance via the
   graph (separate optional `[api]` extra).

## Followup — Implementation Status (2026-06-13)

- **Status: Implementing — Slice 1 shipped.** `sqlmodel>=0.0.14` added to CORE
  dependencies. `agency/_entities.py` (`EntityModels`) derives a SQLModel model
  per ontology label and validates with parity to `ontology.violations`; tests
  green. Not yet wired into `Memory` (additive — zero behaviour change to the
  live record path this slice).
- **Slice 2/3 next:** canonical `table=True` store on graphqlite's shared
  connection + `Memory` wiring + inline `entity_join`; then the FastAPI surface.
- **Doctrine note:** "graph is the store" (CORE.md) holds — the graph stays
  complete; SQLModel adds a typed, SQL-queryable, FastAPI-ready projection of
  the SAME entities in the SAME `.db`, keyed by the graph node id.
