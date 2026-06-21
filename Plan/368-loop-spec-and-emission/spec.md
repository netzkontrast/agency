<!-- agency-node: spec-368 -->
---
spec_id: "368"
slug: loop-spec-and-emission
status: draft
last_updated: 2026-06-21
owner: "@agency"
vision_goals: [7, 9]
depends_on: ["043", "179", "283", "292", "362", "364", "365", "366"]
parent_spec: "362"
affects:
  - agency/_loop.py                        # compile (graph → resolved) + emit (render files)
  - agency/_lifecycle_data/loop/schemas/   # loop.v1 + loop.resolved.v1 (Schema nodes)
  - agency/_lifecycle_data/loop/templates/ # loop.yaml, README, LOOP.md, RUN_IN_SESSION.md
  - agency/capabilities/document/          # reuse document.render / document.sync (no new cap)
domain: loop / document / lifecycle-spine
wave: looper-port
---

# Spec 368 — Loop spec + emission (graph → portable artefacts)

> Child of Spec 362. **Spine-framed (2026-06-21):** the loop lives on the
> lifecycle spine; 368 is its **export surface** — `agency/_loop.py::compile`
> projects the graph-native loop into looper's `loop.resolved.json` shape, and
> **`document.render`** writes `loop.yaml` / `LOOP.md` / `RUN_IN_SESSION.md`.
> Ports looper's `loop.yaml` authoring format, the compile step, the two JSON
> schemas, and the rendered docs. **Frugal:** compile is one function in
> `_loop.py`; everything file-shaped is `document` reused.

## Why

Looper authors in YAML, then **compiles** to a normalized, validated
`loop.resolved.json` (refs expanded, model invocations resolved to argv arrays,
rubrics inlined, `criteria_by_id`/`council_by_id` built — the maps the runner
indexes). The external runner reads ONLY `loop.resolved.json`.

In agency this is `CLAUDE.md` rule 2: **the graph is the source of truth; files
are a peer projection.** A loop's spine nodes (the goal Intent (363),
VerificationCriterion gates (364), council personas (365), the
`Lifecycle{machine:"loop"}` + its control (366)) ARE the loop. `compile`
resolves them into the `loop.resolved.json` shape; `document.render` (Spec
179/283) projects the human files. The **Document is the convergence artefact**
(Spec 292, Goal 9) — each rendered file round-trips back via `document.sync`.

## Design

### The two schemas become agency `Schema` nodes (data)

`loop.v1.schema.json` + `loop.resolved.v1.schema.json` ship verbatim to
`agency/_lifecycle_data/loop/schemas/` and register as agency **Schema** nodes.
The resolved Document `CONFORMS_TO` the resolved schema (Spec 292); `compile`
validates against it before returning. Validation failures are typed findings,
not crashes.

### `_loop.compile` — graph → resolved spec (pure, validated)

A function in the one spine module (`agency/_loop.py`), invoked by the wizard's
emit phase (367) and reachable for direct use:

```python
def compile(ctx, loop_id: str) -> dict:
    """Resolve a graph-native loop into the loop.resolved.json shape:
      - expand refs; build criteria_by_id + council_by_id (the runner's maps)
      - inline each judge criterion's rubric + each gate's criteria
      - resolve every council/host persona to an argv invocation (369 registry)
      - carry loop_control, execution, observability, privacy.egress, workspace
    Validates against loop.resolved.v1 (CONFORMS_TO). Returns
    {resolved, valid: true} or typed validation findings. Pure — no side effects.
    """
```

This is looper's `compile` reading the graph instead of parsing YAML, emitting
the **same** resolved shape — so the ported `run-loop.py` (369) reads it
unchanged. **Round-trip parity is a 362 master Done-When gate.**

### `_loop.emit` + the in-session handoff — via `document.render`

```python
def emit(ctx, loop_id: str, target: str) -> dict:
    """Project the loop to its portable workspace via document.render:
      <target>/loop.yaml          — human-authored form (a Document, re-ingestable)
      <target>/loop.resolved.json — compiled, validated (the runner's contract)
      <target>/LOOP.md            — human rendering + the ASCII flow preview (367)
      <target>/RUN_IN_SESSION.md  — the in-session handoff (the spine-walk contract)
      <target>/loop-workspace/    — empty handoff dir (plan/delivery/review)
      <target>/README.md          — how to run + MIT attribution to looper
    Each rendered markdown carries the <!-- agency-node: <id> --> anchor so an
    on-disk edit round-trips via document.sync (Spec 292). Returns {files:[…]}.
    """
```

`RUN_IN_SESSION.md` renders the **spine-walk** contract: read the resolved spec
+ context, draft the plan artefact, advance the `loop` machine through
plan_gate / delivery_gate honouring the control guards (366), stop on
pass/cap/no-progress. It is looper's §7 in-session handoff, rendered from the
resolved spec — and now also describes *the machine the agent is walking*.

### `loop.yaml` stays human-authored AND re-ingestable (the net gain)

Because `emit` writes real **Documents** (anchored), a human can hand-edit
`loop.yaml` on disk and `document.ingest`/`document.sync` it back into the graph
(keep-both, bi-temporal). Looper's one-way YAML→files becomes a **two-way** peer
surface at no extra authoring cost — the strict win over looper. The
`loop.v1.schema.json` validates the authored form on ingest.

### What 368 does NOT do

- It does not execute the loop (366 walks the machine in-session; 369 runs it
  externally) and does not resolve model CLIs itself — it asks 369's registry
  for the argv. 368 only **renders**.

## Acceptance (Gherkin)

```gherkin
Scenario: compile produces a resolved spec that conforms to the schema
  Given a fully-specified loop on the spine (goal Intent, criteria gates, council, machine+control)
  When I compile it
  Then the result validates against loop.resolved.v1
  And it contains criteria_by_id and council_by_id with inlined rubrics

Scenario: compile resolves every model to an argv invocation
  Given a council persona bound to a model family
  When I compile
  Then that member's invoke is an argv array (never a shell string)

Scenario: emit writes the portable workspace via document.render
  When I emit a loop to ./out
  Then ./out/loop.yaml, loop.resolved.json, LOOP.md, RUN_IN_SESSION.md, README.md, and loop-workspace/ exist
  And each rendered markdown carries an agency-node anchor on its first line

Scenario: an edited loop.yaml round-trips back into the graph
  Given an emitted loop.yaml edited on disk
  When I document.sync it
  Then the loop's spine nodes reflect the edit (keep-both, latest wins on read)

Scenario: compile of an under-specified loop returns typed findings, not a crash
  Given a loop missing a verdict source on a revise_until_clean gate
  When I compile
  Then it returns valid:false with a finding (no exception)
```

## Done When

- [ ] The two looper schemas ship verbatim under `agency/_lifecycle_data/loop/schemas/` and register as `Schema` nodes; the resolved Document `CONFORMS_TO` the resolved schema.
- [ ] `_loop.compile` projects the spine to the resolved shape (criteria_by_id/council_by_id, inlined rubrics, argv invocations) and validates; pure.
- [ ] `_loop.emit` renders loop.yaml/resolved/LOOP.md/RUN_IN_SESSION.md/README + workspace via `document.render`, each anchored.
- [ ] An edited `loop.yaml` round-trips via `document.sync` (the net gain over looper).
- [ ] `tests/acceptance/test_loop_emit.py` covers the scenarios; resolved-shape parity with looper's example fixture asserted.
- [ ] `TODO.md` row updated.

## Followup — Implementation Status (2026-06-21)

**Verdict:** Implemented 2026-06-21 (spine-framed). `_loop.compile` projects the
spine loop into looper's `loop.resolved.json` shape — `criteria_by_id` +
`council_by_id`, inlined judge rubrics, criterion `kind`→`type`, every member
resolved to an argv invocation (never a shell string), derived `stop_conditions`.
Validation reuses `jsonschema` against the vendored self-contained `loop.v1`
schema + the reviewer-only rule (a `revise_until_clean` gate with no
`verdict_source` → typed finding, never a crash). `_loop.emit` writes the portable
workspace (loop.yaml, loop.resolved.json, LOOP.md, RUN_IN_SESSION.md, README.md,
loop-workspace/), each markdown anchored (Spec 292). Both looper schemas +
loop.yaml template vendored under `agency/_lifecycle_data/loop/`. Covered by
`tests/acceptance/test_loop_emit.py` (4 scenarios green). **Frugal: compile/emit
are functions in the one `_loop.py`; file I/O is stdlib + pyyaml.**
**Deferred (honest):** the two-way `document.sync` round-trip (the net gain over
looper) needs full Document binding (register the rendered files as `Document`
nodes `CONFORMS_TO` a `Schema`); the anchor is already emitted, so the round-trip
is a follow-up wiring, not a re-design.

**Prior draft note:** Re-drafted spine-framed (2026-06-21). The export surface: graph →
`loop.resolved.json` via `_loop.compile` (same shape the ported runner reads),
graph → loop.yaml/LOOP.md/RUN_IN_SESSION.md via `document.render` (179/283/292),
with two-way round-trip the net gain over looper's one-way emit. **Frugal:**
compile/emit are functions in the one `_loop.py` module; all file I/O reuses the
`document` capability — no new cap, no new schemas engine. Depends on 364/365/366
(the spine nodes it projects); consumed by 369 (the runner reads its output).
