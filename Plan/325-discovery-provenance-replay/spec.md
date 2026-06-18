---
spec_id: "325"
slug: discovery-provenance-replay
status: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [2, 9]
depends_on: ["002", "292", "307", "308", "320"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 325 — Discovery provenance + replay (`discover.replay`)

> Child of the intent-pillar deep program (Spec 307), **the moat**. Reconstructs
> an entire guided discovery from its provenance — every question asked, every
> citation that grounded it, every reason the WHY changed — as a single ordered
> graph traversal (Goal 2). It is the acceptance test that the whole program's
> provenance is WHOLE; if replay can't reconstruct the discovery, a sibling
> failed to record an edge. Renders to the `discovery-session.md` Document
> (Goal 9).

## Why (evidence + doctrine)

GOALS.md Goal 2 — the **provenance moat** — is the moat: actions recorded against
an intent survive the session as a queryable graph. Spec 307 §"Cross-spec
coherence" rule 6 makes this the program's load-bearing invariant: *"Every
discovery action records its node + edge; 325's replay is the acceptance test
that the moat is whole."* Spec 290 (the read-API) proved an agent can read the
*current state*; this spec proves an agent can reconstruct the *history* — not
"what is the intent now" but **"HOW was this intent discovered — what did we ask,
what did research say, why did the WHY change?"**

That question is unanswerable today: an intent born via `/agency-onboard` (Spec
148) records a `{purpose, deliverable, acceptance}` node and nothing about how it
was reached. The 14 discovery siblings (309–322) each record a node + edge
(`ElicitationTurn`+`ELICITS`, `ClarificationQuestion`+`CLARIFIES`,
`Citation`+`GROUNDS`, `ScopeBoundary`+`BOUNDS`, `AcceptanceCriterion`+`VALIDATES`,
`FeasibilitySignal`, `IntentRefinement`+`REFINES`, all from the Spec 307
ontology). Replay is the **cross-concern-in-one-traversal moat**: it walks all of
those, in `recorded_at`/`PRECEDES` order (Spec 002 bi-temporal substrate), into a
single ordered story of the discovery. The completeness of that story IS the test
that every sibling held up its end of the bargain.

## Design

**Cluster:** `agency/capabilities/discover/clusters/session.py` (Spec 307 verb
table: `replay` → `session` cluster, alongside `state`). **Verb:**

```python
@verb(role="transform")          # read-only — Spec 307 coherence rule 3
def replay(self, session_id: str = "") -> ToolResult:
    """Reconstruct a guided discovery from its provenance — the moat.

    Single ordered traversal of every node a sibling recorded for this
    DiscoverySession: ElicitationTurn (ELICITS), ClarificationQuestion
    (CLARIFIES), Citation (GROUNDS), ScopeBoundary (BOUNDS), AcceptanceCriterion
    (VALIDATES), FeasibilitySignal, IntentRefinement (REFINES) — ordered by
    recorded_at / PRECEDES (Spec 002 bi-temporal). Read-only.
    chain_next: `discover.state` for the current rollup, or render the
    discovery-session.md Document.
    """
```

`role="transform"` (Spec 307 verb table) — read-only, writes nothing (rule 3).
Defaults `session_id` to the session of the serving intent (via
`_base._session_of(ctx.intent_id)`, Spec 308; Spec 091 ambient pattern).

### The traversal (one walk, every concern)

`replay` walks OUT from the `DiscoverySession` node along every recorded edge,
collecting each terminal node with its `recorded_at`, then orders the union by
`recorded_at` (ties broken by the `PRECEDES` chain, Spec 002). The edge set is
the union Spec 307 §"The ontology" declares:

| Edge | Node collected | Step kind |
|---|---|---|
| `ELICITS` | `ElicitationTurn` (beat, kind, question, answer) | `elicit` |
| `CLARIFIES` | `ClarificationQuestion` (text, options, ambiguity_kind) | `clarify` |
| `GROUNDS` | `Citation` (source, claim) — reused from `research` (Spec 044) | `ground` |
| `BOUNDS` | `ScopeBoundary` (item, side) | `scope` |
| `VALIDATES` | `AcceptanceCriterion` (text, gherkin, measurable) | `acceptance` |
| (label) | `FeasibilitySignal` (verdict, rationale) | `feasibility` |
| `REFINES` | `IntentRefinement` (trigger, before, after) | `refine` |

This is the moat's signature: **one traversal answers a cross-concern question**
(what was asked + what research said + why the WHY changed) that would otherwise
need three separate queries. The `IntentRefinement`s (Spec 320, the bi-temporal
supersession trigger, paired with the substrate `SUPERSEDED_BY`) are surfaced
separately as `refinements` — the explicit "why the WHY changed" answer.

### Return shape (ordered story)

```python
{
  "session":     {id, seed, status, clarity_score},
  "intent":      {id, purpose, deliverable, acceptance},   # the DISCOVERED Intent
  "timeline":    [{step, kind, node, summary}, ...],        # every recorded node, in order
  "refinements": [{trigger, before, after, recorded_at}],   # the WHY-change story (Spec 320)
}
```

`timeline` is the durable reconstruction; each entry names the `step` index, the
`kind` (the table above), the `node` id (so the reader can drill), and a derived
`summary` (CLAUDE.md derivability audit — summarised from node props, never
authored). The order is the discovery's actual chronology, not the verb-table
order — a `clarify` that re-entered after `ground` appears where it happened.

### Render to the Document (Goal 9, rule 2)

`replay(..., render=True)` projects the timeline into the `discovery-session.md`
Document (Spec 307 templates; Spec 292 convergence) — the same Document
`discover.state` (Spec 324) renders, but the *history* view rather than the
*current* view. Graph→file on demand; the Document `CONFORMS_TO` the
`discovery-session` Schema (Spec 307) and carries the Spec 292 node anchor. The
Document is where the discovery's provenance becomes a readable, editable peer
surface (Goal 9).

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **Completeness — the moat invariant.** `replay`'s collected edge set EQUALS the
  union of edges every sibling verb recorded for that session — computed from the
  live graph (`ctx.neighbors(session_id, edge)` over each declared edge), never a
  pinned edge list. If a sibling recorded a `BOUNDS` edge, replay surfaces it; if
  replay's set is missing an edge present in the graph, the test fails (a sibling
  recorded but replay didn't traverse — the dormant-edge anti-pattern, CLAUDE.md).
- **Ordered by recorded_at (Spec 002).** The `timeline` is monotonic non-
  decreasing in `recorded_at` — assert each step's `recorded_at >=` its
  predecessor's, derived from the live nodes, not a fixed sequence.
- **Read-only.** `replay` records an Invocation and **no domain node/edge** —
  node-count delta == the single Invocation (same census test as Spec 290 /
  Spec 324).
- **Round-trips a real discovery.** After a `discover.discover` walk (Spec 323)
  that elicited + grounded + clarified + scoped + refined, `replay` reconstructs
  a `timeline` whose `kind` set EQUALS the set of step-kinds the walk actually
  performed (computed from the walk's recorded nodes) — proving the discovery is
  whole. This is the program-level acceptance test.
- **Refinements surface the WHY-change.** A session with an `IntentRefinement`
  (Spec 320) yields a `refinements` entry whose `before`/`after` match the
  superseded/superseding Intent props (the `SUPERSEDED_BY` pair, Spec 002).

## Acceptance

Given any confirmed Intent that was guided-discovered, `discover.replay`
reconstructs the *entire* discovery — every question, every citation, every
feasibility verdict, every scope boundary, every refinement of the WHY — as one
ordered traversal, with **no hand-written Cypher**, and renders it to the
`discovery-session.md` Document. If replay cannot reconstruct a discovery, that
is the signal a sibling (309–322) failed to record an edge — making this spec the
program's whole-provenance acceptance gate (Spec 307 rule 6).

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** The moat child of Spec 307. Lands LAST (or alongside the
  build-out) because its completeness test depends on every sibling having
  recorded its edge — it is the integration check, not a leaf feature. Depends on
  the bi-temporal substrate (Spec 002) for ordering, the scaffold (308) for
  `_session_of`, Spec 320 for `IntentRefinement`/`REFINES`, and Spec 292 for the
  render target.
- **Build slice:** the traversal + ordered return first (Slice 1); the
  `discovery-session.md` render (Slice 2) sharing the Document with Spec 324's
  current-state view (one Document, two projections — history vs. now).
- **Why it is the acceptance gate:** the completeness invariant is *computed from
  the live graph* (CLAUDE.md #8) — so when a future sibling adds an edge, replay
  must traverse it or the test reds. This keeps "declare an edge ⇒ traverse it"
  (CLAUDE.md dormant-surface audit) enforced for the whole `discover` ontology.
