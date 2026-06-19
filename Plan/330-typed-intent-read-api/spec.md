---
spec_id: "330"
slug: typed-intent-read-api
status: Shipped
last_updated: 2026-06-19
owner: "@agency"
vision_goals: [2, 4, 5]
depends_on: ["290", "326", "327", "328", "329"]
domain: intent
wave: program-master
parent_spec: "326"
---

# Spec 330 — The typed Intent read API (joins, not Cypher)

> Slice 4 of Spec 326. Lands `IntentStore` — a typed-join read surface over the
> four-concept tables — and wires `manage`/`analyze` to it, so the moat is read
> through typed joins instead of hand-written Cypher (and is FastAPI-ready, Goal 5).

## Why

Slices 327–329 made the interweave a set of typed tables with FK columns + the
`Edge` spine. The value is realised only when something *reads* the joins (the
dormant-surface audit: a typed column nothing queries is dead weight). This slice
is the consumer: one read API that answers the four-pillar questions Spec 290's
`manage` answers today via `analyze.graph`/`memory.provenance`/Cypher — now as
typed joins. It is also the surface a FastAPI frontend binds to (Goal 5/7 — the
original Spec 289 directive).

## Design

### `IntentStore` (`agency/_entity_store.py`, beside `EntityStore`)

A read-only OOP handle bound to the same shared connection, exposing typed joins:

```python
class IntentStore:
    def serves(self, intent_id) -> list[Invocation]:
        """Every capability invocation mapped to this intent (the directive's core)
        — `WHERE serves_intent_id = :id`, with the Agent joined in."""

    def intent_tree(self, root_id) -> list[Intent]:
        """The PARENT_INTENT sub-intent tree (recursive on parent_intent_id)."""

    def provenance(self, intent_id) -> dict:
        """The cross-concern join CORE.md names: invocations + their agents +
        produced artefacts + lifecycle state — one query over the typed tables
        and the Edge spine, not a Cypher traversal."""

    def fulfilment(self, intent_id) -> dict:
        """Is the intent fulfilled? The latest acceptance/completion Gate verdict
        + the AcceptanceCriterion satisfaction (Spec 328) — the typed answer to
        'are we there yet?'."""
```

Each method is a typed SQL join over the 326 tables; returns the SQLModel rows (or
a budgeted projection) — FastAPI-serialisable directly (Goal 5).

### Wire `manage`/`analyze` to it (no second source — Spec 290 rule)

`manage` (Spec 290: `state`/`open_intents`/`whats_next`/`research_state`/
`artefacts`/`timeline`) currently composes `analyze.graph` + `memory.provenance` +
Cypher. Where a `manage` answer is now a typed join, route it through `IntentStore`
— the typed tables become the read substrate, the graph stays write-authoritative.
This is a *composition* swap (Spec 290's "no second source of truth"), not a new
query language: `manage.provenance(intent)` calls `IntentStore.provenance(intent)`.

### Parity gate (the safety net)

`IntentStore` is a projection; its answers MUST equal the authoritative graph's.
A parity test asserts each method's result-set equals the equivalent Cypher
traversal for the same intent — so a typed read can never silently diverge from
the moat. If they disagree, the mirror (327–329) has a bug; the test catches it.

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **`serves` completeness:** `IntentStore.serves(Q)` returns exactly the
  `Invocation`s whose graph `SERVES` edge targets Q — set-equality with the
  Cypher traversal, computed live.
- **`provenance` parity (the moat):** `IntentStore.provenance(Q)` (typed join)
  equals the `memory.provenance`/Cypher result for Q — invocations, agents,
  artefacts, lifecycle — no divergence (the projection is faithful).
- **`fulfilment` reads the Intent-owned Gate (Spec 328):** `fulfilment(Q)`
  reports `fulfilled` iff the latest acceptance/completion `Gate.status == passed`
  and all `measurable` criteria satisfied — flips when the gate row changes.
- **`intent_tree` matches PARENT_INTENT:** the typed recursive tree equals the
  graph's `PARENT_INTENT` subtree for the root (Spec 048) — same nodes.
- **`manage` uses the typed path:** a `manage` provenance/state answer routed
  through `IntentStore` equals its pre-wiring result — the swap is behaviour-
  preserving (Spec 290 parity).

## Acceptance

An agent (or a FastAPI frontend) reads the whole interweave through typed joins —
"every capability serving this intent, its agent, its artefacts, its lifecycle,
and whether it's fulfilled" — via `IntentStore`, with a parity gate guaranteeing
the typed projection never diverges from the authoritative graph. The moat is now
legible as typed relations, not just Cypher.

## Followup — Implementation Status (2026-06-19)

- **Status: SHIPPED 2026-06-19.** Slice 4 — the read API + the consumer that makes
  327–329's typed columns load-bearing. Done:
  - `agency/_entity_store.py` — `IntentStore` (bound to the shared engine):
    `serves` (typed Invocations for an Intent), `intent_tree` (the PARENT_INTENT
    subtree over `parent_intent_id`), `provenance` (invocations + agents +
    produced/serving artefacts + lifecycle — one typed query set), `fulfilment`
    (latest Intent-owned Gate verdict — acceptance/completion wins over clarity —
    + criteria counts). Returns plain dicts (FastAPI-serialisable).
  - `agency/memory.py` — exposes `memory.intents = IntentStore(self.entities)`.
  - `agency/capabilities/manage/_main.py` — `manage.state(for_intent_id)` now
    surfaces a typed `fulfilment` block via `memory.intents` (the real consumer —
    not dormant surface; additive field, no new wire verb → no install regen).
  - `tests/acceptance/{features/typed_read_api.feature,test_typed_read_api.py}` —
    5 scenarios incl. the **parity gate**: `serves` and `provenance.invocations`
    equal the live Cypher SERVES-Invocation set (the typed projection never
    diverges from the graph), `intent_tree` follows PARENT_INTENT, `fulfilment`
    carries the gate verdict, and `manage.state` surfaces the fulfilment block.
- **Decision (the spec's YAGNI default):** wired the headline `fulfilment` read
  into `manage.state` now; the broader `provenance`/`open_intents`/`whats_next`
  re-route stays a follow-up (the existing Cypher paths are parity-equivalent and
  untouched, so no regression risk taken for no present need).
- **FastAPI (Goal 5/7):** `IntentStore`'s dict returns are the read models a
  FastAPI app exposes — the next follow-up now the four slices have landed.
