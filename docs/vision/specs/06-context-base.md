---
slug: spec-context-base
type: spec
status: ready
summary: The store — the GraphQLite-backed Store singleton, the Artefact-driver REGISTRY, the pre/post-tool hooks, and the Artefact node payload. GraphQLite is the only substrate; no sidecar files, no raw-SQLite fallback.
---

# 06 — Context base (the store)

The store lives in `context/`. It is the only persistent state. A capability's
context aspect — its memory — materializes here lazily as `Artefact` and memory
nodes the moment it first produces or learns.

## Store (singleton, GraphQLite-only)

```python
get_store() -> Store        # process singleton

class Store:
    boot() -> None                                                   # idempotent open-or-create of ontology.db; zero seed nodes
    upsert_node(node_id: str, payload: dict, *, label: str) -> None
    upsert_edge(src: str, dst: str, payload: dict | None = None, *, rel_type: str) -> None
    query(cypher: str, params: dict | None = None) -> list[dict]     # direct GraphQLite pass-through
    log_tool_call(tool: str, envelope: dict) -> None                 # append-only provenance
```

GraphQLite is the only substrate. If it fails to load, the store raises rather
than falling back.

## Artefact-driver REGISTRY

```python
# context/_drivers/__init__.py
REGISTRY: dict[str, ArtefactDriver]
register(key: str, driver: ArtefactDriver) -> None   # KeyError on duplicate unless AGENCY_DRIVER_OVERRIDE=1
resolve(key: str) -> ArtefactDriver                  # KeyError (listing available keys) on miss
```

`fs` is the only mandatory driver; `repo` / `s3` / `http` / `drive` follow.

## Hooks

- **PreToolUse** — `validate_envelope_in(tool_name, args)`: manifest-writing
  tools are validated against the aspect schemas ([01](01-manifest.md)).
- **PostToolUse** — validation-first pipeline:
  1. validate `data.artefact_metadata` against `artefact-node.schema.json`
  2. resolve `artefact_driver` via `REGISTRY` **before** upsert
  3. upsert the `Artefact` node
  4. persist bytes via the driver (if present)
  5. ingest `data.emitted_edges[]`

## Artefact node

```
label: Artefact
required: content_type, sha256, size_bytes, created_at, produced_by, derived_from
optional: artefact_driver, driver_pointer, capability, satisfies_phase
```

No `.meta.json` sidecar is ever written to user storage — these fields are
graph properties.
