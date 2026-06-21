---
spec_id: "329"
slug: typed-lifecycle-memory-spine
status: Shipped
state: done
last_updated: 2026-06-19
owner: "@agency"
vision_goals: [2, 3, 4]
depends_on: ["326", "327"]
domain: intent
wave: program-master
parent_spec: "326"
---

# Spec 329 — Typed Lifecycle state + the Memory provenance spine

> Slice 3 of Spec 326. Lands `LifecycleState` (the session state machine) and the
> Memory spine — `Artefact` + the general typed `Edge` table — so the full
> interweave is traversable by SQL join, not just the hot FK columns.

## Why

Slice 327 wove Capability → Intent (`serves_intent_id`) and named the `Agent`.
This slice completes the interweave's other two concepts: **Lifecycle** (what the
task/session is doing right now — `submitted → working → … → completed`) and
**Memory** (the provenance spine). The hot FK columns (327/328) cover the
constantly-traversed relationships; the `Edge` table mirrors **every** typed edge
so any provenance question — GROUNDS · CLARIFIES · SUPERSEDED_BY · DISPATCHED_TO ·
ELICITS · … — is a typed query. This is what makes CORE.md's "single-traversal
cross-concern provenance" a *typed* single traversal.

## Design

### Tables (`agency/_entities.py`, `table=True`; cite Spec 326)

```python
class LifecycleState(SQLModel, table=True):      # Lifecycle concept
    __tablename__ = "agency_lifecycle_state"
    id: str = Field(primary_key=True)
    state: str = Field(index=True)               # enum ← ontology
                                                 #   (submitted/working/input-required/
                                                 #    completed/failed/canceled)
    serves_intent_id: str = Field(foreign_key="agency_intent.id", index=True)
    agent_id: str | None = Field(default=None, foreign_key="agency_agent.id")
    vfrom: int = 0
    vto: int = OPEN

class Artefact(SQLModel, table=True):            # Memory concept
    __tablename__ = "agency_artefact"
    id: str = Field(primary_key=True)
    kind: str = Field(index=True)
    produced_by_id: str | None = Field(default=None, foreign_key="agency_invocation.id")
    serves_intent_id: str | None = Field(default=None, foreign_key="agency_intent.id")
    vfrom: int = 0
    vto: int = OPEN

class Edge(SQLModel, table=True):                # Memory spine — every typed edge
    __tablename__ = "agency_edge"
    id: str = Field(primary_key=True)            # synthetic (src|rel|dst|tick)
    src_id: str = Field(index=True)
    dst_id: str = Field(index=True)
    rel: str = Field(index=True)                 # enum ← ontology (SERVES/PRODUCES/…)
    vfrom: int = 0
    vto: int = OPEN
```

### Mirror router extension (Spec 327's hook)

- Core node labels `Lifecycle`/`Artefact` → their typed tables (router gains two
  arms). `Artefact.produced_by_id` is set from the `PRODUCES` edge; its
  `serves_intent_id` from `SERVES`.
- **Every** `Memory.link(src, dst, rel)` writes (or supersedes) an `Edge` row —
  this is the general spine. The hot FK columns (327/328 + `produced_by_id` here)
  are an *index* over the most-traversed rels; `Edge` is the complete set, so a
  rel without a dedicated FK column (GROUNDS/CLARIFIES/…) is still a typed query.
- One-way, post-authoritative-write, failure-isolated (289's contract).

### Declare an edge ⇒ traverse it (dormant-surface audit)

The `Edge` table is only worth its write cost if it is read. Slice 330's read API
traverses it (`provenance`, `fulfilment`); this slice's tests assert the spine is
*complete* (every graph edge has its `Edge` row) so 330 can rely on it. A typed
edge nothing joins on would be dormant surface — 330 is its consumer.

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **Spine completeness:** the count of `Edge` rows (current, `vto == OPEN`) equals
  the count of live graph edges — computed from both, never pinned; a new
  `link` adds exactly one `Edge` row.
- **Artefact provenance:** an `Artefact.produced_by_id` resolves to the
  `Invocation` that produced it (its `PRODUCES` edge), and that Invocation's
  `serves_intent_id` chains to the same Intent the Artefact serves — the
  PRODUCES→SERVES chain is a join.
- **Lifecycle weaves to Intent + Agent:** every `LifecycleState.serves_intent_id`
  resolves to an `Intent`; its `agent_id` (when set) resolves to the SAME `Agent`
  the performer's `Invocation`s reference (one performer identity, Spec 327).
- **Cross-concern in one join:** "every Invocation serving intent Q, its Agent,
  its Artefacts, and the Lifecycle state" returns the same set as the equivalent
  Cypher traversal from Q — typed join and graph agree (no divergence).
- **One-way + failure-isolated:** a forced mirror error on an `Edge`/`Artefact`
  leaves the graph edge committed — graph stays authoritative.

## Acceptance

The four concepts are fully typed and joined: Lifecycle state and the Memory spine
(`Artefact` + every `Edge`) weave back to Intent alongside Capability, so the
moat question CORE.md names — "every action that SERVES intent Q, the agent, the
gate, the artefact" — is one typed SQL join over rows mirrored one-way from the
authoritative graph.

## Followup — Implementation Status (2026-06-19)

- **Status: SHIPPED 2026-06-19.** Slice 3 — completes the interweave. Done:
  - `agency/_entity_store.py` — `TypedLifecycleState` (state · phase ·
    `serves_intent_id` · `agent_id`), `TypedArtefact` (kind · `produced_by_id` ·
    `serves_intent_id`), and `TypedEdge` (the spine: `src_id` · `dst_id` · `rel`,
    id == `src|rel|dst`). New REVERSE-direction FK map `_EDGE_FK_DST`
    (`PRODUCES` → `produced_by_id` on the dst Artefact, **only** when the src is an
    `Invocation` — an Intent-produced artefact keeps it null). New methods
    `upsert_edge_row` / `edge_rows` / `edge_row`; `set_fk_from_edge` now handles
    both SRC- and DST-direction FKs via the shared `_set_fk` helper.
  - `agency/memory.py` — `link` captures the edge tick once and projects the edge
    onto BOTH its typed FK AND the `TypedEdge` spine after the authoritative edge
    write (one-way, failure-isolated).
  - `tests/acceptance/{features/typed_spine.feature,test_typed_spine.py}` — 6
    scenarios: Artefact `produced_by_id`+`serves_intent_id` FKs, the Intent-produced
    artefact keeps `produced_by_id` null, Lifecycle weaves to its Intent, spine
    completeness (every live graph edge ⊆ the typed spine), +1 row per link, and
    one-way failure-isolation (a forced spine error leaves the graph edge).
- **Decisions:** the spine keys edges by `src|rel|dst` (current row; the graph
  holds full bi-temporal edge history) — `vfrom`/`vto` present for a later as-of
  read. `serves_intent_id` reuses the existing `SERVES` src-FK (Lifecycle/Artefact
  share the column; the row-existence check disambiguates).
- **Next:** Slice 330 — the `IntentStore` typed-join read API + the parity gate,
  the consumer that makes these columns load-bearing (dormant-surface audit).
