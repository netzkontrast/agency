---
spec_id: "327"
slug: typed-intent-capability-core
status: draft
last_updated: 2026-06-19
owner: "@agency"
vision_goals: [2, 4, 5]
depends_on: ["289", "326"]
domain: intent
wave: program-master
parent_spec: "326"
---

# Spec 327 — Typed Intent + Capability core (map all capabilities into intents)

> Slice 1 of Spec 326. Lands the three core typed tables — `Intent`,
> `Invocation`, `Agent` — and the mirror router that fills them, realising the
> directive's heart: **every capability invocation maps to the intent it serves.**

## Why

Spec 326 §"The interweave" makes "map all capabilities into intents" a typed
invariant: `Invocation.serves_intent_id` is NOT NULL → a FK to its `Intent`.
Today that mapping exists only as a graph `SERVES` edge — invisible to a typed
join and to a FastAPI reader (Goal 5). This slice is the load-bearing one:
`Intent` is the hub, `Invocation` is the capability call, `Agent` is the performer
(Jules/`develop`/`subagent` — Capability-owned per the owner directive), and the
mirror router is what keeps the rows true to the authoritative graph.

## Design

### Tables (`agency/_entities.py`, `table=True`; cite Spec 326 schema)

```python
class Intent(SQLModel, table=True):
    __tablename__ = "agency_intent"
    id: str = Field(primary_key=True)            # graph node id
    purpose: str
    deliverable: str
    acceptance: str
    status: str = Field(index=True)              # enum ← ontology (draft/confirmed/…)
    owner: str                                   # enum ← ontology (user/agent/…)
    clarity_score: float | None = None           # Spec 322 (recorded on confirm)
    parent_intent_id: str | None = Field(default=None, foreign_key="agency_intent.id")
    vfrom: int = 0
    vto: int = OPEN

class Agent(SQLModel, table=True):               # Capability concept (owner directive)
    __tablename__ = "agency_agent"
    id: str = Field(primary_key=True)
    kind: str = Field(index=True)                # enum ← ontology (claude/jules/subagent/develop/…)
    status: str | None = None

class Invocation(SQLModel, table=True):
    __tablename__ = "agency_invocation"
    id: str = Field(primary_key=True)
    capability: str = Field(index=True)
    verb: str = Field(index=True)
    role: str                                    # enum ← ontology (act/transform/effect)
    serves_intent_id: str = Field(foreign_key="agency_intent.id", index=True)   # NOT NULL
    agent_id: str | None = Field(default=None, foreign_key="agency_agent.id")
    vfrom: int = 0
    vto: int = OPEN
```

Enums are **not** re-declared — the column stays `str` and validity is enforced by
289's `EntityModels.validate` (which reads `Ontology.enums`), so there is one
source for the allowed sets (rule 2). FK columns are the new typed structure.

### The mirror router (extend Spec 289's hook in `Memory`)

`Memory` already mirrors each authoritative write to `EntityStore`. Extend that
one hook to **route by label**: a core label (`Intent`/`Invocation`/`Agent`) →
its typed table; everything else → the generic `EntityRecord` (unchanged). On a
`link(src, dst, "SERVES")` the router sets `Invocation.serves_intent_id`; on
`link(.., "BY")` it sets `agent_id`; on `link(.., "PARENT_INTENT")` it sets
`Intent.parent_intent_id` (the hot FKs are filled from the edges the graph
already records). One-way, post-authoritative-write, failure-isolated (a mirror
error never fails the graph write — 289's contract).

### The mapping invariant

Because every Invocation node is recorded with a serving intent (the engine
injects `ctx.intent_id` per call — CORE.md), the mirror sets `serves_intent_id`
on every `Invocation` row. The invariant **"no capability invocation is unmapped
from an intent"** becomes checkable in SQL: `SELECT count(*) FROM agency_invocation
WHERE serves_intent_id IS NULL` is 0.

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **Mirror parity:** after N authoritative `record`s of core entities, each has
  exactly one typed row whose `id` == the graph node id — counts read from the
  live graph + tables, never pinned.
- **The mapping invariant (the directive):** every `Invocation` row has a
  non-null `serves_intent_id` that resolves to a real `Intent` row — assert the
  NULL-count is 0 and each FK joins, computed from the live tables.
- **`serves_intent_id` tracks SERVES:** an Invocation's FK equals the target of
  its graph `SERVES` edge (no divergence between the typed column and the edge).
- **Agent is Capability-owned + shared:** an `Invocation.agent_id` and a
  (Spec 329) `LifecycleState.agent_id` for the same performer resolve to the SAME
  `Agent` row — one performer identity.
- **One-way + failure-isolated:** a forced mirror error leaves the graph write
  committed (the graph node exists; the typed row is absent) — the graph stays
  authoritative.
- **Enum sourcing (rule 2):** an out-of-enum `role`/`owner` is rejected by the
  shared `EntityModels.validate` (the ontology), not a second hand-copied set.

## Acceptance

After this slice, every capability invocation is a typed `Invocation` row with a
foreign key to the `Intent` it serves and the `Agent` that ran it — "all
capabilities mapped into intents" is a NOT-NULL FK invariant, queryable by join,
mirrored one-way from the authoritative graph.

## Followup — Implementation Status (2026-06-19)

- **Status: draft.** Slice 1 of the Spec 326 program — the core mapping. Build
  FIRST; slices 328 (fulfilment), 329 (lifecycle + spine), 330 (read API) hang
  off these tables + the mirror router.
- **Open question (resolve at build):** whether superseded (`vto != OPEN`)
  versions get their own rows or only the current version mirrors. Default:
  mirror the current version (the typed tables are the "now" projection; the graph
  holds full bi-temporal history) — revisit if a typed as-of read is needed.
