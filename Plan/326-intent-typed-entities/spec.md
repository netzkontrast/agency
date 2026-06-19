---
spec_id: "326"
slug: intent-typed-entities
status: draft
last_updated: 2026-06-19
owner: "@agency"
vision_goals: [2, 4, 5, 7]
depends_on: ["048", "286", "289", "322"]
domain: intent
wave: program-master
---

# Spec 326 — Intent-centric typed SQLModel entities (the four-concept interweave)

> **Program master.** Extends Spec 289 (the derive-from-ontology SQLModel
> foundation) with an **explicit, relational typed layer**: one SQLModel
> `table=True` class per four-concept core entity, with real **foreign-key
> columns** that weave **Capability · Lifecycle · Memory** back to **Intent**.
> Where 289 mirrors every node into one generic `EntityRecord` JSON blob, this
> makes the *core* entities clear typed tables whose relationships are queryable
> by SQL joins — so "every capability invocation maps to its intent, and is the
> intent fulfilled?" is a typed join, not hand-written Cypher.
>
> Governs slices 327–330 until each ships (Spec 047 precedent).

## Why (evidence + doctrine + the directive)

**Owner directive (2026-06-19):** *"We need clear datastructures that live in
SQLModel for the intent — map all capabilities into intents — interweaving
capabilities with a Lifecycle and Memory."* Two refinements during design: **the
Gate lives in Intent** (a gate captures *whether the intent is fulfilled*), and
**the Agent lives in Capability** (Jules · `develop` · `subagent` are capability
performers, not a Lifecycle-only concept; their session *state* stays Lifecycle).

**What exists (Spec 289).** `agency/_entities.py` DERIVES a `table=False`
validation model per ontology label; `agency/_entity_store.py` mirrors every
graph node into ONE generic `EntityRecord` table (`id · label · data(JSON) ·
vfrom · vto`), a one-way projection FROM the authoritative graph. That gives
typed *validation* and a generic blob mirror — but **no typed relationships**:
the SERVES / PRODUCES / PARENT_INTENT structure lives only as graph edges, so
"all invocations serving intent Q, their agents, the gate it passed, the
artefacts produced" is a Cypher traversal, never a typed join, and the relational
shape an agent (or a FastAPI frontend, Goal 5/7) reads is opaque JSON.

**The doctrine this serves.** Goal 2 (the provenance moat) is only as legible as
the structure that reads it. CORE.md frames Intent as the **human-owned root**
every concept edges back to via SERVES. This spec makes that interweave a typed,
relational fact: the four concepts become tables, and Intent is the hub every FK
points at. The graph stays write-authoritative (provenance, bi-temporal history,
ontology enforcement, rule 2 "no parallel tracking system"); these tables are a
**richer one-way mirror** of the *core* entities — re-derivable, never a second
source.

## Architecture — a typed projection FROM the authoritative graph

```
            Memory.record / link / update / supersede        (graph = authority:
                       │  authoritative graph write            provenance, bi-temporal,
                       ▼                                        ontology enforcement)
            ┌──────────────────────────────┐
            │   one-way mirror hook (289)   │  ── core label?
            └──────────────────────────────┘        │           │ no
                       │ yes (core entity)           │           ▼
                       ▼                              │     EntityRecord (289 generic
        the TYPED four-concept tables (326)           │     JSON blob — domain/music/
        on the SAME shared SQLite connection          │     novel/etc. nodes keep this)
        (node id == row PK; JOIN-able inline)         ▼
                                            link(rel) → Edge row (+ hot FK update)
```

- **One shared DB** (Spec 289 advice): the typed tables bind to graphqlite's own
  SQLite connection (`creator=`/`StaticPool`), so they live in the one `.db`,
  JOIN-able to graph nodes; the node id IS the row PK.
- **One-way, failure-isolated:** the mirror runs AFTER the authoritative graph
  write; a projection failure never fails the graph write (289's contract,
  unchanged).
- **Hybrid:** typed tables for the four-concept *core*; the generic
  `EntityRecord` for everything else (domain caps) — we don't hand-author a table
  per domain label (YAGNI + rule 2).
- **Enums derive from the ontology** (rule 2 — single source): `status` · `owner`
  · `role` · `state` · `rel` reference the existing `Ontology.enums`, never a
  hand-copied list. The *relational* structure (the FKs) is the new typed layer
  the flat ontology can't express.

## The typed tables (the datastructures)

All `SQLModel, table=True` in `agency/_entities.py` (alongside 289's
`EntityModels`); `id` is the graph node id; `vfrom`/`vto` mirror the bi-temporal
window.

### Intent concept — the WHY *and whether it is fulfilled*

| Table | Columns | Mirrors |
|---|---|---|
| `Intent` | `id` PK · purpose · deliverable · acceptance · status* · owner* · `clarity_score` · `parent_intent_id`→Intent | Intent node + PARENT_INTENT |
| `AcceptanceCriterion` | `id` PK · `intent_id`→Intent · text · gherkin · measurable | AcceptanceCriterion + VALIDATES (Spec 317) |
| `Gate` | `id` PK · `intent_id`→Intent · kind* (`clarity`\|`acceptance`\|`completion`) · status* (`pending`\|`passed`\|`failed`) · score · threshold · checked_at | the fulfilment verdict (Spec 322) |

> **Gate lives in Intent** (owner directive): a gate records *whether the intent
> is fulfilled* — the **clarity** gate at capture (reads `clarity_score`, Spec
> 322) and the **acceptance/completion** gate at done-time (reads the
> `AcceptanceCriterion`s). It is the typed home + history of the gate we already
> ship on `Intent.confirm`.

### Capability concept — every invocation, mapped to its intent + agent

| Table | Columns | Mirrors |
|---|---|---|
| `Invocation` | `id` PK · capability · verb · role* (`act`\|`transform`\|`effect`) · **`serves_intent_id`→Intent (NOT NULL)** · `agent_id`→Agent | Invocation + SERVES + BY |
| `Agent` | `id` PK · kind* (`claude`\|`jules`\|`subagent`\|`develop`\|…) · status | Agent node |

> **Agent lives in Capability** (owner directive): Jules · `develop` · `subagent`
> are capability performers. `Agent` is referenced by BOTH `Invocation`
> (who/what acted) and `LifecycleState` (whose session) — the single tie between a
> performer, the capability it ran, and the lifecycle it's in. **"Map all
> capabilities into intents" = the `serves_intent_id` NOT-NULL invariant:** no
> Invocation row exists without a FK to the Intent it serves.

### Lifecycle concept — the session state machine

| Table | Columns | Mirrors |
|---|---|---|
| `LifecycleState` | `id` PK · state* (`submitted`\|`working`\|`input-required`\|`completed`\|`failed`\|`canceled`) · `serves_intent_id`→Intent · `agent_id`→Agent | Lifecycle node |

### Memory concept — the typed provenance spine

| Table | Columns | Mirrors |
|---|---|---|
| `Artefact` | `id` PK · kind · **`produced_by_id`→Invocation** · `serves_intent_id`→Intent | Artefact + PRODUCES |
| `Edge` | `id` PK · `src_id` · `dst_id` · `rel`* · vfrom · vto | EVERY typed edge (full traversal) |

`*` = enum sourced from `Ontology.enums`. The **hot FK columns**
(`serves_intent_id`, `agent_id`, `produced_by_id`, `parent_intent_id`) are the
fast path for the relationships traversed constantly; the **`Edge` table** mirrors
*all* edges (GROUNDS · VALIDATES · CLARIFIES · SUPERSEDED_BY · DISPATCHED_TO ·
ELICITS · …) so any traversal is a typed query, not just the hot four.

## The interweave (the answer to the directive)

Intent is the hub; the three other concepts weave back through FKs:

```
                         ┌───────────────── Intent ─────────────────┐
                         │  (purpose/deliverable/acceptance/clarity) │
         owns ───────────┤                                           ├─────────── owns
   AcceptanceCriterion   │                                           │   Gate (is it fulfilled?)
                         └───▲───────────▲───────────────▲──────────┘
            serves_intent_id │           │ serves_intent  │ serves_intent
                  ┌──────────┴──┐   ┌─────┴────────┐  ┌────┴─────────┐
   Capability ──▶ │ Invocation  │   │ LifecycleState│  │  Artefact    │ ◀── Memory
                  │  agent_id ──┼──▶│  agent_id ───┼─▶│ produced_by  │
                  └─────────────┘   └──────┬───────┘  └──────────────┘
                                           ▼
                                   Capability ──▶ Agent (jules/develop/subagent)
                                           ▲
                                    Memory ─┴─ Edge (every rel, full spine)
```

One SQL join now answers the moat question — *"every capability that SERVES
intent Q, the agent that ran it, the gate it passed, the artefact it produced"* —
that CORE.md names as the thing a flat SDK+memory stack cannot do in one hop.

## Slices (each a child spec, shippable on its own)

| Slice | Spec | Delivers |
|---|---|---|
| 1 — core mapping | **327** | `Intent` · `Invocation` · `Agent` tables + the `serves_intent_id` mapping + the mirror router in `Memory` (the "all capabilities → intents" core) |
| 2 — fulfilment | **328** | `Gate` · `AcceptanceCriterion` (Intent-owned), the typed home of the Spec 322 confirm gate + a Gate-check history |
| 3 — lifecycle + spine | **329** | `LifecycleState` + the `Artefact`/`Edge` Memory spine (full typed traversal) |
| 4 — read API | **330** | `IntentStore` typed-join read API (`serves` · `intent_tree` · `provenance` · `fulfilment`) + wire `manage`/`analyze` to it instead of Cypher |

## Done When (program-level — children carry their own)

- [ ] All four slices (327–330) drafted with `## Why`, `## Design`, `## Tests`
      (rule-8 invariants), `## Acceptance`, `## Followup`.
- [ ] The schema + enum sourcing here is the single reference the children cite
      (no child redefines a table/FK).
- [ ] The graph stays write-authoritative; the typed tables are a one-way,
      failure-isolated mirror (289's contract holds).
- [ ] `TODO.md` carries the program row + the four child rows.

## Acceptance

A reviewer (or a FastAPI frontend — Goal 5/7) can read the four concepts as typed
tables, follow every capability invocation to the intent it serves and the agent
that ran it by FK, ask "is this intent fulfilled?" from its Intent-owned `Gate`,
and reconstruct full provenance with SQL joins — while the graph remains the sole
write-authority and the typed rows are re-derivable from it.

## Followup — Implementation Status (2026-06-19)

- **Status: draft (program master).** Designed via the brainstorming discipline
  (owner-confirmed: typed projection from the authoritative graph · full
  four-concept interweave · Gate→Intent · Agent→Capability). Extends the shipped
  Spec 289 Slices 1–2. No code yet.
- **Next:** Slice 327 (Intent + Capability core + mirror router) first — it
  realises "map all capabilities into intents" and everything else hangs off it.
