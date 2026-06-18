---
spec_id: "324"
slug: discovery-read-api-management
status: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [1, 9]
depends_on: ["290", "292", "307", "308", "322"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 324 — Discovery read-API + management/dashboard (`discover.state`)

> Child of the intent-pillar deep program (Spec 307), **read side**. The
> dashboard that answers "what's captured, what's still ambiguous, what's
> grounded, how confident are we?" for a discovery — a budgeted projection
> (Goal 1) that COMPOSES the Spec 290 `manage` read-API and the Spec 322 clarity
> score, never reimplementing them, and renders to the `discovery-session.md`
> Document (Goal 9).
>
> **★ EXTENDED by Spec 307 §Refinement (2026-06-18).** `state` absorbs `replay`
> (325) as **`state(mode=now|history)`** — same Document, two projections — with the
> history mode composing the shipped `manage.timeline`. One read verb for the whole
> discovery read side.

## Why (evidence + doctrine)

Spec 307's flow has a write side (interview · ground · clarify · frame · examine ·
scope · refine) but no **read side**: mid-discovery an agent cannot ask *"where
are we — what has the session captured, what's still open, how grounded is the
intent, are we clear enough to confirm?"* without stitching together the session
turns, the clarity inputs, and the grounding citations by hand. Spec 290 already
proved the doctrine for the *whole graph* — the Memory/Lifecycle read-suite is a
first-class tooled surface, read-only, token-budgeted, composing
`analyze.graph`/`memory.provenance`/`project` rather than re-querying (Spec 290
§"Decisions": *"Generalize, don't duplicate… no second source of truth"*). The
provenance moat is only as valuable as the API that reads it.

`discover.state` is the discovery-scoped peer of `manage.state`: it answers the
same "where are we" question, but for ONE guided-discovery session rather than
the whole graph. Spec 307 §"Cross-spec coherence" rule 4 binds it explicitly —
*"`state` composes `manage` / `analyze.graph` / `project`; it never reimplements
a query that exists"* — and the coverage matrix names this child the one that
exercises the `manage` read-API (Spec 290) and the budgeted projection (Goal 1:
AskUser collapses N research turns into one question; `state` collapses the whole
session into one ranked, budget-fitting view).

## Design

**Cluster:** `agency/capabilities/discover/clusters/session.py` (Spec 307 verb
table: `state` → `session` cluster). **Verb:**

```python
@verb(role="transform")          # read-only — Spec 307 coherence rule 3
def state(self, intent_id: str = "") -> ToolResult:
    """Discovery dashboard — what's captured / ambiguous / grounded / confident.

    Composes the manage read-API (Spec 290) + the clarity score (Spec 322) +
    the session's ElicitationTurns into ONE budgeted projection. Defaults to the
    serving intent (ctx.intent_id, the Spec 091 ambient pattern). Reads only;
    records the single Invocation and no domain node/edge.
    chain_next: `discover.clarify` on the top open ambiguity, or — if clarity
    clears the Spec 322 gate — `discover.discover` advances to `decide`.
    """
```

### What it composes (no second source of truth — Spec 290 rule)

`state` is pure composition over surfaces that already exist:

- **Open intent + acceptance + SERVES subtree** ← `manage.open_intents` /
  `manage.state` (Spec 290) — NOT re-queried.
- **Grounding citations** ← `manage.research_state` filtered to the `GROUNDS`
  edges on this Intent (Spec 307 ontology; `GROUNDS` reuses the `research`
  `Citation`, Spec 044) — NOT a fresh citation scan.
- **Artefacts + timeline** ← `manage.artefacts` / `manage.timeline` (Spec 290)
  scoped to the session's intent.
- **Clarity score** ← `discover.clarity` (Spec 322) — the single confidence
  number, read not recomputed.
- **Session turns + open ambiguities** ← the session's `ElicitationTurn`s
  (via `_base._session_of(intent_id)`, Spec 308) and the
  `ClarificationQuestion`s not yet answered (`ambiguity_kind` enum, Spec 307).

The seam: this is the **only child besides 321** that touches code outside
`discover/` — and it touches it only by *calling* `manage` verbs through
`ctx.call`, never by reaching into `manage`'s queries. That is the documented
composition seam (Spec 307 §"drop-in bar" + §"Cross-spec coherence" rule 1).

### The budgeted projection (Goal 1)

Returns a ranked, budget-fitting delta — never a raw subgraph (Spec 290 §"Token-
budgeted projections", same `project(query, budget)` discipline):

```python
{
  "intent":              {id, purpose, deliverable, acceptance, status},
  "clarity":             {score, threshold, gate_clears: bool},          # Spec 322
  "ambiguities_open":    [{kind, text}, ...],          # unanswered ClarificationQuestions
  "citations_grounding": [{source, claim}, ...],       # GROUNDS edges (budgeted)
  "scope":               {in: [...], out: [...]},      # ScopeBoundary BOUNDS edges
  "acceptance":          [{text, gherkin, measurable}, ...],  # VALIDATES edges
  "turns":               <count + last-N summaries>,   # ElicitationTurns, budgeted
  "recommended_next":    "<the chain_next cue>",        # derived from what's missing
}
```

`recommended_next` is **derived** (CLAUDE.md derivability audit), not authored:
it reads what's missing (no citations → `ground`; open ambiguities → `clarify`;
clarity below threshold → keep clarifying; all present + gate clears → `decide`)
— the same "surface the acceptance as the next action" pattern `manage.whats_next`
ships (Spec 290 followup).

### Markdown dashboard (rule 2 — render from graph, Spec 292)

`state(..., render=True)` (or a thin `discover.render` alias mirroring
`manage.render`, Spec 290 Slice 2) projects the same data into the
`discovery-session.md` Document (Spec 307 templates; Spec 292 convergence) — the
human-readable "where are we in this discovery" view. Render is graph→file on
demand; it adds no node beyond the Document binding (Spec 292 `<!-- agency-node:
<id> -->` anchor). The Document IS the convergence artefact (Goal 9): it binds
its `template`/`schema`, `CONFORMS_TO` the `discovery-session` Schema (Spec 307),
and renders the four-concept view of the discovery for the Session.

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **Read-only invariant (the Spec 290 test, scoped).** Invoking `discover.state`
  records an Invocation but **adds no domain node/edge** — node-count delta ==
  the single Invocation (census before/after, computed, never a frozen count).
  Mirrors `test_manage_read_api_adds_no_domain_node` (Spec 290 followup).
- **No second source of truth.** `state`'s open-intent + acceptance figures
  AGREE with `manage.open_intents` / `manage.whats_next` on the same intent —
  assert equality of the composed fields, proving `state` did not re-query
  (Spec 290 §"Composition" test, applied here).
- **Budget respected (Goal 1).** The projection fits the budget — assert
  `len(projection) <= budget` (or token-count via Spec 082 `count_tokens`),
  derived from the live graph, never a pinned size.
- **Clarity is read, not recomputed.** `state`'s `clarity.score` equals
  `discover.clarity`'s score for the same intent (single source — Spec 322), and
  `gate_clears` is monotonic in that score.
- **Render round-trips (Goal 9).** `state(render=True)` produces a
  `discovery-session.md` with the Spec 292 node anchor and `CONFORMS_TO` the
  `discovery-session` Schema — and re-reading it via `document.ingest` recovers
  the projection (the Document is the same fact as the graph view).

## Acceptance

An agent mid-discovery answers "what's captured / what's still ambiguous / what's
grounded / how confident are we / what's next" through one `discover.state` call
with **no hand-written Cypher and no re-implemented `manage` query**, gets a
budget-fitting projection, and can render it to the `discovery-session.md`
Document on demand. The read suite for the Intent pillar's discovery is complete
and composes — not duplicates — the Spec 290 read-API.

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** Read-side child of Spec 307. Lands after the scaffold (308)
  for `_base._session_of` and after Spec 322 (clarity) so the confidence number
  exists; composes the already-Shipped Spec 290 `manage` read-API.
- **Build slice:** the composing projection first (Slice 1), the markdown render
  (Slice 2) mirroring `manage.render`'s graph→file-on-demand pattern — same
  two-slice shape Spec 290 shipped.
- **Decision reconciled with Spec 290:** the verb table marks `state`
  `role="transform"`, but Spec 290's shipped read verbs use `role="act"` with the
  read-only invariant enforced *by test, not by the role tag* (Spec 290 followup
  §"Decisions reconciled"). Resolve at build: match the sibling surface
  (`role="act"`) and keep the read-only test as the guarantee. The budget is a
  named `top`/`limit` param (Spec 290 house style), not a magic number.
