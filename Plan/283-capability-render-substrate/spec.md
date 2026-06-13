---
spec: 283
title: capability-render-substrate
status: Drafting
depends_on: [020, 124, 149, 278]
clusters: [core, render, observability]
vision_goals: [2, 4, 7]
---

# Spec 283 — Capability Render Substrate (graph → markdown rendered view)

> **One-line:** every capability renders its graph state into a complete set of
> markdown files (frontmatter + templates) in a per-capability directory tree,
> **auto-rendered on every mutation**, each file captured as an `Artefact` node —
> closing CLAUDE.md rule 2 ("the graph is the store; files are a rendered view")
> across the whole capability surface. **Novel is the reference implementation.**

## Why (evidence + doctrine)

1. **Rule 2 is unenforced.** The graph is canonical, but rendering to disk is
   ad-hoc per capability. Novel writes via `FileNovelStateDriver`
   (`agency/capabilities/novel/drivers_production.py`), music via its own
   `FileStateDriver` — **each hand-rolls the same `_parse_frontmatter` /
   `_render_template` logic**, and a brand-new capability inherits none of it.
   The "drop-in capability" bar (CLAUDE.md) says adding a folder should give a
   complete capability; today it does NOT give file rendering.

2. **Graph/disk provenance is split (Workstream F).** The Kohärenz-Protokoll
   graph has **2 `Artefact` nodes for 41 on-disk chapter files**. Disk writes by
   the state driver don't mint `Artefact` nodes, so the file tree is a SECOND
   source of truth with no provenance link back to the graph. There is no single
   "this file was rendered from node X" story.

3. **Spec 278 covers the metadata, not the dispatch.** Spec 278
   (universal-frontmatter-discipline, *drafted*) ships the frontmatter SCHEMA +
   `agency/_frontmatter.py` round-trip + a regression gate. It does NOT define
   *who renders*, *where files land per capability*, *when re-render happens*, or
   *Artefact capture on render*. **283 is the render/dispatch/auto-mint layer
   that consumes 278's frontmatter discipline.** They are complementary; 283
   `depends_on` 278's frontmatter helper.

## Decisions (user, 2026-06-13)

- **What:** a rendered markdown VIEW — graph projected to disk, frontmatter +
  templates, per-capability directory structure. The graph stays canonical.
- **Mechanism:** a SHARED render substrate every capability adopts uniformly
  (not per-capability bespoke). Novel is the reference; other caps plug in.
- **Trigger:** **auto-render on every mutation** — a successful mutating
  (`effect`-role) verb re-renders its affected file(s) as a side effect, so disk
  is always in sync with the graph. (A full-rebuild verb complements it for
  ground-truth re-materialization, replacing `scripts/materialize_manuscript.py`.)

## Design

### 1. `RenderSpec` — how a capability maps graph entities to files

A capability declares, on its `OntologyExtension` (or a new `render` attribute),
a list of `RenderRule`s. Each rule binds a node `label` to:

- `output_path(node, ctx) -> str` — path RELATIVE to the capability's render root
  (e.g. a Chapter → `chapters/{number:02d}-{slug}.md`).
- `template` — the template id under `agency/capabilities/<cap>/templates/`.
- `frontmatter(node, ctx) -> dict` — the typed frontmatter (a 278 `GraphSlice`
  shape: includes the node `id` + its key edges, so `from_frontmatter` round-trips).
- `body(node, ctx) -> str` — the rendered body (template-filled or a
  graph-aggregate like `render_manuscript`).
- `parent_edge` (optional) — the edge whose change should also re-render this
  node (e.g. a new Scene re-renders its parent Chapter's brief).

The reference `novel` ruleset covers `Novel` (`work.md`), `Chapter`
(`chapters/NN-slug.md`), `Scene` (`scenes/NN-slug.md`), and the existing
manuscript/synopsis renders.

### 2. `RenderDriver` protocol (substrate)

`agency/_render.py` defines `RenderDriver`:

- `write(path: str, frontmatter: dict, body: str) -> Path` — writes the file
  (frontmatter via `agency/_frontmatter.py`, Spec 278) under the resolved root,
  idempotent (byte-identical re-render is a no-op write).
- `root(cap_name: str, ctx) -> Path` — the per-capability output root.

Two implementations mirror the established driver pattern (Spec 117/124):

- `FileRenderDriver` (production) — wraps the existing `FileNovelStateDriver`
  layout for novel; generic path join for other caps.
- `FakeRenderDriver` (tests) — deterministic in-memory map, no disk; records a
  call log for assertions (mirrors `FakeFormatDriver`).

### 3. Per-capability output convention

`<content_root>/<capability>/...` — `content_root` resolves via the capability's
config (the `NovelConfig`/`MusicConfig` 4-level resolution generalized into a
substrate `render_root` lookup). Novel keeps its current
`works/{author}/works/{genre}/{slug}/` sub-layout via its `RenderRule.output_path`.
The convention is declared, not hard-coded per verb — adding a capability with a
`RenderSpec` gives it file rendering for free (the drop-in bar).

### 4. Auto-render on mutation (the trigger)

A hook in `Registry.invoke` (the same boundary that records the Invocation):
after an `effect`-role verb returns success, if the capability has a `RenderSpec`
AND a `RenderDriver` is wired AND the verb touched a renderable label, the engine:

1. resolves the affected node(s) (the verb's returned id + `parent_edge` walk),
2. renders each via its `RenderRule`,
3. `RenderDriver.write(...)`,
4. records an `Artefact{kind, path, entity_id, frontmatter_hash}` + `PRODUCES`
   edge from the Invocation (closing Workstream F).

**Guards (so this is safe + opt-in):**
- No `RenderSpec` on the capability → no-op (every cap that doesn't want files is
  untouched — the 91-verb wire contract is unchanged).
- No production `RenderDriver` wired (bare unit-test engine) → no-op (graph-only,
  preserving the existing `_novel_production` flag semantics).
- Render failure is recorded as a `transient`/`permanent` warning on the
  Invocation (Spec 282 severity), NEVER aborts the mutating verb — the graph
  write already succeeded and is canonical; the file is a derived view.
- Idempotent: re-rendering an unchanged node writes byte-identical output.

### 5. Full-rebuild verb

A substrate `render_capability(cap_name, root_id)` (and a novel
`render_all(novel_id)` convenience) re-materializes the ENTIRE file tree from
graph ground truth — idempotent, the canonical recovery path. Replaces the
out-of-band `scripts/materialize_manuscript.py`.

### 6. Frontmatter round-trip (with Spec 278)

Every rendered file carries 278-shaped frontmatter including the node `id` and
its parent edge, so `from_frontmatter(path)` reconstructs the graph slice and a
re-render is byte-identical. 283 ships the MINIMAL `agency/_frontmatter.py`
(parse/emit/hash) if 278 hasn't landed; 278's discipline (schema-per-kind,
baseline gate) extends it. **Build 278 + 283 together or 278 first.**

## Tests (RED → GREEN, when implemented)

- `RenderRule` for a Chapter produces the expected path + frontmatter (with node
  id + CHAPTER_OF parent) + body.
- `from_frontmatter(render(node)) == graph_slice(node)` — round-trip property.
- Auto-render: `create_chapter` through the wired engine writes the file AND
  mints an `Artefact` + `PRODUCES` edge (Workstream F closure assertion).
- Auto-render is a NO-OP on a bare engine (no driver) and on a cap without a
  `RenderSpec` (the 91-verb contract is untouched — regression guard).
- A render failure records a Spec-282 warning but the mutating verb still
  returns success and the graph node persists.
- `render_capability` rebuilds a full novel tree byte-identically from ground
  truth (idempotent).
- Drift guard: # of `Artefact(kind=…)` nodes for a rendered novel == # of files
  on disk (the inverse of the evidence's 2-for-41 drift).

## Acceptance

- A capability with a `RenderSpec` + wired `RenderDriver` auto-renders complete
  markdown files (frontmatter + template) on every mutation, in its own
  directory tree, with every file captured as an `Artefact`.
- Novel is the reference: editing/creating any novel entity keeps the
  `Manuscript/` tree and the graph in lockstep, one provenance story.
- `from_frontmatter` round-trips (rule 2 closure).
- Adding file rendering to a NEW capability = declaring a `RenderSpec` and
  nothing else (the drop-in bar holds).
- Bare engines + non-rendering caps are unaffected.

## Open questions (resolve during implementation brainstorm)

- **OQ1 — render granularity vs. write cost.** Auto-render on EVERY effect verb
  means each mutation does disk I/O. For a hot batch (the ingest's hundreds of
  beats) this multiplies writes. Options: (a) render synchronously always; (b)
  debounce/coalesce per execute-block (render once at block end); (c) a
  `render=False` opt-out arg on hot-path verbs. Lean (b) — coalesce per
  invocation batch — but needs an engine seam. Decide before coding.
- **OQ2 — relationship to Spec 278 module ownership.** Who ships
  `agency/_frontmatter.py` — 278 or 283? Recommend 278 ships it; 283 depends.
  If 283 lands first, 283 ships the minimal version and 278 extends.
- **OQ3 — non-novel caps in scope for the first slice?** Recommend Slice 1 =
  substrate + novel reference ONLY; music + others adopt in Slice 2.

## Followup — Implementation Status (2026-06-13)

- **Status: Drafting (design only).** Research complete (rendering/frontmatter
  landscape mapped: Spec 278 drafted, novel `FileNovelStateDriver` + templates,
  duplicated frontmatter parsers, ~6-9 Artefact kinds across 100+ verbs, no
  per-cap output convention). Scope decided with user (rendered view · shared
  substrate · auto-on-mutation). Awaiting user review of this spec before the
  implementation plan + TDD.
