---
spec_id: "289"
slug: management-capability
status: draft
last_updated: 2026-06-13
owner: "@agency"
vision_goals: [1, 2, 4]
depends_on: ["020", "042", "045", "048"]
---

# Spec 289 — Management capability (the four-pillars read-API)

> Born from the Core Vision addition (`docs/vision/CORE.md` §"Four complete
> pillars", owner directive 2026-06-13): each of Intent · Capability ·
> Lifecycle · Memory needs a **complete suite of code + tools** — write *and*
> read. The write/act sides are mature; the **read/manage** side is the gap.
> This spec is the keystone that closes it — the first "complete a pillar" build.
>
> Spec number **289**: 288 was claimed by the refactor agent’s
> `sqlmodel-entity-store` (built on PR #141); this renumber yields to it and
> clears the 287 planning-skill reservation. Claimed numbers are tracked in
> `Plan/_planning/vision-program-master-plan.md` to prevent future collisions.

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

## Followup — Implementation Status (2026-06-13)

- **Status: draft (Vision-side).** Authored by the Vision owner as the keystone
  of the four-pillars Core Vision. **Build is feature work** — to be brainstormed
  + spec-panelled, then implemented (likely after the Vision realignment +
  the OOP refactor settle). Not yet started.
