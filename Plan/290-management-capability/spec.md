---
spec_id: "290"
slug: management-capability
status: Shipped
last_updated: 2026-06-17
owner: "@agency"
vision_goals: [1, 2, 4]
depends_on: ["020", "042", "045", "048"]
---

# Spec 290 — Management capability (the four-pillars read-API)

> Born from the Core Vision addition (`docs/vision/CORE.md` §"Four complete
> pillars", owner directive 2026-06-13): each of Intent · Capability ·
> Lifecycle · Memory needs a **complete suite of code + tools** — write *and*
> read. The write/act sides are mature; the **read/manage** side is the gap.
> This spec is the keystone that closes it — the first "complete a pillar" build.
>
> Spec number **290**: 288 then 289 both collided with the refactor agent’s
> `sqlmodel-entity-store` (a double-yield); 289 is theirs, this is 290. See the
> claimed-numbers registry in `Plan/_planning/vision-program-master-plan.md`.

## Why (evidence + doctrine)

An agent today cannot ask *"what is the current state — open intents, lifecycle
status, research, artefacts — across the whole graph?"* without either raw
Cypher (`ctx.memory.g.query`) or stitching three partial surfaces:

- `analyze.graph` — a census + typed listing (counts, not a stateful rollup),
- `memory.provenance` — one-intent traversal (drills, doesn't survey),
- the planned `navigate` read-projection (specced, unbuilt).

That violates the Core Vision's "complete suite per pillar": the **read side**
of Memory + Lifecycle is not a first-class, tooled surface. The provenance moat
(Goal 2) is only as valuable as the API that reads it; a token-budgeted read-API
(Goal 1) over the open node set (Goal 4) is the missing half.

## Decisions

- **Generalize, don't duplicate.** This capability *composes* `analyze.graph`,
  `memory.provenance`, `project`, and the `navigate` projection into one
  coherent read-API — it does not reimplement them. Land it as the `navigate`
  cluster's completion (alias `manage`), per `CAPABILITY-CLUSTERS.md`.
- **Read-only.** Every verb is `role="transform"` — no writes, no new node
  types. It reads the existing graph; it never mutates the moat.
- **Token-budgeted projections** (Goal 1) — every verb returns a ranked,
  budgeted delta via `project(query, budget)`, never a raw dump; render markdown
  on demand (rule 2).
- **One verb per pillar question**, so the read-suite mirrors the four pillars.

## Design — the read-API surface (draft verb set)

| Verb | Pillar | Returns |
|---|---|---|
| `state(intent_id="")` | cross | a current-state rollup: active intent(s), lifecycle status, open gates, recent artefacts — the "where are we" dashboard |
| `open_intents(status="")` | Intent | open/in-flight intents + their acceptance + the `SERVES` subtree size |
| `whats_next(intent_id)` | Lifecycle | blocked items + next actions against the intent's acceptance (the `navigate` core) |
| `research_state(domain="")` | Memory | leads · claims · citations · pending verifications, grouped |
| `artefacts(intent_id="")` | Memory | artefacts PRODUCED under an intent, with their source invocations |
| `timeline(intent_id="")` | Lifecycle · Memory | the ordered Lifecycle/Gate/Phase events (`PRECEDES`/`PASSED`) for an intent |

(Verb names + the exact projection shapes are a brainstorm/spec-panel output;
this table is the scope, not the frozen surface.)

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- Read-only: invoking any `manage` verb records an Invocation but **adds no
  domain node/edge** (graph node-count delta == the single Invocation).
- Coverage: the verb set touches all four pillars' node types (Intent ·
  Invocation · Lifecycle/Gate · Artefact · Reflection/Claim).
- Budget: each projection respects `project`'s budget (returns a delta, not the
  raw subgraph) — assert `len(projection) <= budget`, computed from the live
  graph, never a frozen count.
- Composition: `whats_next` agrees with `navigate`/`provenance` on the same
  intent (no divergent second source of truth).

## Acceptance

- An agent answers "current state / open intents / research / what's next /
  artefacts / timeline" through `manage` verbs with **no hand-written Cypher**.
- The Memory + Lifecycle **read-suites are complete** per CORE.md §"Four
  complete pillars"; `CAPABILITY-CLUSTERS.md` `navigate`/`manage` flips from
  "completion target" to built.
- Zero new writes / node types; wire contract unchanged (it's new verbs on the
  open Capability set, Goal 4 — adding a folder).

## Followup — Implementation Status (2026-06-17)

- **Status: Shipped.** The full six-verb read-API lands on the `manage`
  capability (read + write folded onto one capability, per Spec 293's
  decision). All four pillars' read-suite is now complete.

**Done (verb → file:line, `agency/capabilities/manage/_main.py`):**
- `state(for_intent_id="")` — cross-pillar rollup (live Intent/Reflection/
  Artefact counts + Lifecycle-by-state; scoped SERVES subtree + artefacts
  when an intent is named). Folded via Spec 293.
- `open_intents(top=20)` — live Intents + acceptance + SERVES subtree size,
  busiest-first. Folded via Spec 293.
- `timeline(for_intent_id, limit=100)` — ordered Event + Invocation history.
  Folded via Spec 293.
- `artefacts(for_intent_id)` — Artefacts PRODUCED under an intent. Folded via
  Spec 293.
- **`whats_next(for_intent_id)` (NEW, this branch)** — the navigate core:
  Lifecycles/Gates serving the intent split into `blocked` (input/auth-
  required, failed, unpassed gates, explicit `BLOCKED_ON` deps) vs in-flight
  `next` (submitted/working); with neither and the acceptance unmet, the
  acceptance itself is surfaced as the next action. `done` derives from
  Intent.status or all-Lifecycles-terminal.
- **`research_state(domain="", top=20)` (NEW, this branch)** — composes the
  research sub-graph (`Research`·`ResearchClaim`·`Citation`·`Verification`)
  into one grouped rollup; `domain` filters leads by question + scopes the
  children; `pending` = leads not yet `ready`/`published`.

**Tests** — `tests/acceptance/features/manage.feature` (+2 scenarios) +
`tests/acceptance/test_manage.py`: `whats_next` echoes acceptance + a next
action; `research_state` groups a lead with its citation + lists it pending;
plus `test_manage_read_api_adds_no_domain_node` enforcing the read-only
invariant (six read verbs add an Invocation but zero domain nodes — asserted
against a live census, not a frozen count, per rule 8).

**Decisions reconciled with the draft table:**
- Roles use `role="act"` (matching the four sibling read verbs Spec 293
  already shipped) rather than the draft's `role="transform"` — consistency
  with the existing surface; the read-only invariant is enforced by test, not
  by the role tag.
- Budgeting via a `top`/`limit` param (the house style the sibling verbs set)
  rather than a `project(query, budget)` call — the draft table was "scope,
  not the frozen surface".

**Slice 2 (shipped 2026-06-17):** `manage.render(for_intent_id="", top=5)` —
the markdown dashboard projection (rule 2: graph→markdown on demand). Composes
`state` + `open_intents` (+ `whats_next` when an intent is named) into the
human-readable "where are we" view the spec's `state` row describes. Read-only
(calls the sibling read verbs; the read-only invariant test covers it). +1
acceptance scenario.

**Still (optional):** `whats_next` could cross-check against a built `navigate`
projection once that lands (today it IS the navigate core); a real
`project(query, budget)` token-budgeting primitive (specced-but-unbuilt) would
replace the `top`/`limit` bound across the read-suite.
