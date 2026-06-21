---
spec_id: "368"
slug: loop-spec-and-emission
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [7, 9]
depends_on: ["043", "179", "283", "292", "362", "364", "365", "366"]
parent_spec: "362"
domain: loop / document
wave: looper-port
---

# Spec 368 — Loop spec + emission (graph → portable artefacts)

> Child of Spec 362. Ports looper's **`loop.yaml` authoring format**, the
> **compile to `loop.resolved.json`**, the two JSON **schemas**, and the rendered
> **`LOOP.md`** + **`RUN_IN_SESSION.md`**. This is the **export surface** of the
> native-first/export-second reconciliation (master §"The reconciliation"): the
> graph-native loop projected OUT to portable files via `document.render`.

## Why

Looper authors in YAML (`loop.yaml` — human/comment-friendly), then **compiles** to
a normalized, validated `loop.resolved.json`:

> "Looper compiles it to a normalized, validated `loop.resolved.json` (refs
> expanded, model invocations resolved to argv arrays, rubrics inlined).
> `RUN_IN_SESSION.md` is rendered from that resolved spec. **The external runner
> only ever reads `loop.resolved.json`.**"

The resolved spec carries the maps the runner indexes (`criteria_by_id`,
`council_by_id` — seen in `run-loop.py`), the inlined rubrics, and argv-resolved
invocations. Two JSON Schemas validate the two forms (`loop.v1.schema.json` 190
LOC, `loop.resolved.v1.schema.json` 25 LOC).

In agency this is `CLAUDE.md` rule 2 made concrete: **the graph is the source of
truth; files are a peer projection.** A loop's nodes (LoopGoal, VerificationCriterion,
CouncilMember, LoopControl, EgressPolicy, the Lifecycle machine) ARE the loop;
`loop.compile` resolves them into the `loop.resolved.json` shape, and
`document.render` (Spec 179/283) projects `loop.yaml` / `LOOP.md` /
`RUN_IN_SESSION.md`. The **Document is the convergence artefact** (Spec 292, Goal
9) — it binds the loop's `template` + `schema` and round-trips.

## Design

### The two schemas become agency `Schema` nodes

`schemas/loop.v1.schema.json` and `schemas/loop.resolved.v1.schema.json` ship
verbatim into `agency/capabilities/loop/schemas/` and are registered as agency
**Schema** nodes. The resolved-spec Document `CONFORMS_TO` the resolved schema
(Spec 292 binding); `compile` validates against it before returning. Validation
failures are typed, not crashes.

### `loop.compile` — graph → resolved spec (pure, validated)

```python
@verb(role="transform")
def compile(self, ctx, loop_id: str) -> dict:
    """Resolve a graph-native loop into the loop.resolved.json shape.
      - expand refs; build criteria_by_id + council_by_id (the maps the runner indexes)
      - inline each judge criterion's rubric + each gate's criteria
      - resolve every council/host model to an argv invocation (via 369 registry)
      - carry loop_control, execution, observability, privacy.egress, workspace
    Validates against loop.resolved.v1 (CONFORMS_TO). Returns
    {resolved: {...}, valid: true} or typed validation findings. No side effects
    — pure projection. chain_next: loop.emit to write files, loop.emit_runner (369).
    """
```

This is looper's `compile` (`scripts/looper.py`), but reading the graph instead of
parsing YAML — and emitting the *same* resolved shape, so the ported `run-loop.py`
(369) reads it unchanged. **Round-trip parity is a master Done-When gate.**

### `loop.emit` + `render_handoff` — `document.render` to files

```python
@verb(role="effect")
def emit(self, ctx, loop_id: str, target: str) -> dict:
    """Project the loop to its portable workspace via document.render:
      <target>/loop.yaml             — human-authored form (Document, re-ingestable)
      <target>/loop.resolved.json    — compiled, validated (the runner's contract)
      <target>/LOOP.md               — human rendering + the ASCII flow preview (367)
      <target>/loop-workspace/       — empty handoff dir (plan/delivery/review live here)
      <target>/README.md             — how to run + MIT attribution to looper
    Each rendered file carries the <!-- agency-node: <id> --> anchor so edits
    round-trip back via document.sync (Spec 292). Returns {files:[…]}.
    """

@verb(role="effect")
def render_handoff(self, ctx, loop_id: str, target: str) -> dict:
    """Render RUN_IN_SESSION.md — the default in-session execution handoff:
    read loop.resolved.json/LOOP.md + context sources, draft plan.md, run the
    plan gate, revise <= cap, write delivery-N, run the delivery gate, keep the
    loop machine current, stop on pass/cap/no-progress. This is looper's §7
    in-session contract rendered from the resolved spec. Returns {path}."""
```

`emit` uses `document.render` (graph→file, Spec 179) so the files are real agency
**Documents** with the `<!-- agency-node: <id> -->` anchor — meaning a human can
edit `loop.yaml` on disk and `document.sync` it back into the graph (keep-both,
bi-temporal). Looper's one-way YAML→files becomes a **two-way** peer surface — a
strict net gain over looper, at no extra authoring cost.

### `loop.yaml` stays human-authored AND re-ingestable

A user (or another tool) can hand-write `loop.yaml`; `document.ingest` +
`loop.compile`-from-ingested reconstructs the graph nodes. This preserves looper's
"author in YAML" path while making the graph the canonical store. The
`loop.v1.schema.json` validates the authored form on ingest.

### What 368 does NOT do

- It does not execute the loop (366 walks it in-session; 369 runs it externally).
- It does not resolve model CLIs itself — it asks 369's registry for argv
  (separation: 368 renders, 369 owns the boundary to external processes).

## Acceptance (Gherkin)

```gherkin
Scenario: compile produces a resolved spec that conforms to the schema
  Given a fully-specified loop in the graph
  When I compile it
  Then the result validates against loop.resolved.v1
  And it contains criteria_by_id and council_by_id maps with inlined rubrics

Scenario: compile resolves every model to an argv invocation
  Given a council member bound to a model family
  When I compile
  Then that member's invoke is an argv array (never a shell string)

Scenario: emit writes the portable workspace via document.render
  When I emit a loop to ./out
  Then ./out/loop.yaml, loop.resolved.json, LOOP.md, README.md, and loop-workspace/ exist
  And each rendered markdown carries an agency-node anchor on its first line

Scenario: an edited loop.yaml round-trips back into the graph
  Given an emitted loop.yaml edited on disk
  When I document.sync it
  Then the loop's graph nodes reflect the edit (keep-both, latest wins on read)

Scenario: render_handoff produces the in-session contract
  When I render_handoff
  Then RUN_IN_SESSION.md describes the plan-gate / delivery-gate walk with the caps inlined

Scenario: compile of an under-specified loop returns typed findings, not a crash
  Given a loop missing a verdict source on a revise_until_clean gate
  When I compile
  Then it returns valid:false with a finding (no exception)
```

## Done When

- [ ] The two looper schemas ship verbatim and register as agency `Schema` nodes; the resolved Document `CONFORMS_TO` the resolved schema.
- [ ] `loop.compile` projects the graph to the resolved shape (criteria_by_id/council_by_id, inlined rubrics, argv invocations) and validates; pure, no side effects.
- [ ] `loop.emit` renders loop.yaml/resolved/LOOP.md/README + workspace via `document.render`, each with the round-trip anchor.
- [ ] `loop.render_handoff` renders RUN_IN_SESSION.md from the resolved spec.
- [ ] An edited `loop.yaml` round-trips via `document.sync` (the net gain over looper).
- [ ] `tests/acceptance/test_loop_emit.py` covers the scenarios; resolved-shape parity with looper's example fixture asserted.
- [ ] `TODO.md` row updated.

## Followup — Implementation Status (2026-06-20)

**Verdict:** Not started — drafted under the 362 wave. The export surface: graph →
`loop.resolved.json` (same shape the ported runner reads) via `loop.compile`, and
graph → loop.yaml/LOOP.md/RUN_IN_SESSION.md via `document.render` (179/283/292) —
with two-way round-trip the net gain over looper's one-way emit. Depends on 364/
365/366 (the nodes it projects); consumed by 369 (the runner reads its output).
