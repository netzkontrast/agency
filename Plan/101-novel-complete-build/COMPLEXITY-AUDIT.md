# Complexity audit — what a "very complex novel" needs

> Iteration 2 audit (2026-06-07). The user requested the design hold a
> **very complex novel**. This file enumerates the 12 complexity axes a
> production novel hits and maps each to the spec changes that land in
> iteration 2.

## The 12 complexity axes

| # | Axis | Example | Spec change |
|---|---|---|---|
| 1 | **Multi-volume / Series structure** | 10-book epic; Vol I = 3 Parts × 7 Books | 102 — add `Volume`, `Part`, `Book` nodes (Series → Volume → Part → Book → Chapter → Scene) |
| 2 | **Multi-POV (5+ POV characters)** | A Song of Ice and Fire, 31 POVs | 102 — `Scene.pov_character`; 104 — per-POV voice signatures + POV-balance gate; 108 — `pov-balance` gate |
| 3 | **Nested storyforms / subplots** | The main story + 4 subplots, each with its own Dramatica argument | 103 — `Subplot` node + nested `Storyform`; H1-H12 apply per-Storyform |
| 4 | **Non-linear narrative** | Flashbacks, parallel timelines, frame story | 102 — `Chapter.narrative_order` + `Chapter.story_time`; 104 — chronological-reorder verb; 108 — timeline-consistency gate |
| 5 | **Worldbuilding depth** | Magic system + 5 cultures + 3 religions + 2 languages | 102 — `World` sub-graph: `Culture`, `Religion`, `Language`, `MagicSystem`, `Politics`, `Economy`, `Geography`, `Bestiary`, `WorldAxiom`, `Canon` |
| 6 | **Large cast (50+ characters)** | All the houses of ASOIAF; LOTR's fellowship + adversaries | 102 — `Faction`/`House`/`Family` nodes; `Character.parent_faction`; 106 — cast-hierarchy report |
| 7 | **Character voice evolution** | Protagonist's voice darkens over the arc; first chapter ≠ last chapter | 104 — `voice_signature` versioned per arc-position; 106 — voice-drift report tracking |
| 8 | **Multilingual canon** | German canon NOT translated (kohaerenz directive); multilingual character speech | 101 — explicit ADR: canon prose preserved in source language; 102 — `Chapter.canon_language`; 104 — translation-refusal discipline |
| 9 | **Character arcs across volumes** | Stark arc spans 5 books; growth-by-volume | 102 — `Arc` node; `Arc.phases[]`; 106 — arc-coverage report |
| 10 | **Series-level coherence** | Same character, different books — same age math, same world rules, same prior events | 106 — `series_coherence_check` (already declared); 108 — `series-publish-ready` gate |
| 11 | **Genre-blending** | Fantasy + mystery + romance; thriller + literary | 102 — `Novel.genres: list[str]` (already supported); 105 — multi-domain research dispatch |
| 12 | **Provenance at scale** | 500K words, 200+ chapters, 1000s of revisions | (substrate concern — Spec 020 graph scales; spec changes minimal) |

## ADRs (architecture decision records)

### ADR-1: Canon language preservation

The capability MUST NOT translate canon prose into any other language
(carried from the kohaerenz normative spec §N.2.6). German canon stays
German; English translation drafts are SEPARATE artefacts with
`generated_by` metadata. Test asserts that a `translate_prose` verb does
NOT exist on the capability.

### ADR-2: Storyform-per-Subplot

Each subplot gets its own Storyform sub-graph (full 4 throughlines + 4
classes + 8 archetype slots, scoped to the subplot's cast). The decidability
matrix runs PER Storyform. Cross-storyform coherence (subplot resolution
must serve OS goal) is a separate `cross_storyform_check` verb.

### ADR-3: Narrative-time vs Story-time distinction

Every Chapter + Scene carries TWO orderings:
- `narrative_order`: the position in the reader-facing manuscript (sjuzhet)
- `story_time`: a stamp on the in-world timeline (fabula)

Verbs that need chronological order (continuity check, character-age
math) use `story_time`. Verbs that need reading order (POV balance,
voice-drift) use `narrative_order`. The schema enforces both fields on
the node.

### ADR-4: World as a typed sub-graph

A novel's `World` node owns a typed sub-graph with closed taxonomy:
`Culture`, `Religion`, `Language`, `MagicSystem`, `Politics`, `Economy`,
`Geography`, `Bestiary`. Each subschema node carries a `body` field
(markdown) and edges. `WorldAxiom` nodes carry facts the prose must
respect; `Canon` edges link prose passages to the axioms they
encode/establish. This is the graph form of the bitwize/kohaerenz
"world-bible.md" file — but graph-canonical, file-derived per CLAUDE.md
rule 2.

### ADR-5: Volume / Part / Book hierarchy is opt-in

Simple novels: Novel → Chapter → Scene (3 levels, current 102 design).
Complex novels: Novel → Volume → Part → Book → Chapter → Scene (6 levels).
A Novel carries an `outline_hierarchy: ["chapter", "scene"]` field that
declares its depth. The lifecycle verbs (create_volume, create_part,
create_book) only register when the hierarchy includes them. Default
hierarchy is the simple form.

### ADR-6: POV-character first-class

Scene already has `pov_character`. iteration 2 promotes this to a
first-class concern: `check_pov_consistency` (104) is per-POV;
`pov_balance_gate` (108) enforces "no POV exceeds 40% unless the novel's
type-of-narrative is 'first-person-protagonist'".

## What does NOT change

- The 5-driver set (StateDriver/TextDriver/DBDriver/CloudDriver/
  FormatDriver) — sufficient for every complexity axis.
- The provenance moat — every iteration-2 node type SERVES the intent.
- The 11 decidability checks in 103 — run PER Storyform; subplots get
  their own Storyform sub-graph and the same 11 checks fire on each.
- The walkable-skill discipline — the only addition is new phase-shapes
  for complex novels (e.g. `multi-pov-revision` is an opt-in skill,
  not a replacement for `scene-revision`).

## Implementation phase priority (when 102 PR lands)

The iteration-2 additions are **back-loaded**: simple novels work with
the existing schema; complex-novel features activate when the user opts
in via novel frontmatter (`outline_hierarchy`, `multilingual`,
`pov_count`, `subplot_count`). Phase ordering:

1. 102 ships with all iteration-2 nodes declared but optional. Tests
   prove a simple-novel fixture and a complex-novel fixture both pass.
2. 103 ships with per-Subplot Storyform support but the `cross_storyform_
   check` is a v2 verb (out of scope for the initial wave).
3. 104 ships POV-aware checks. POV-balance gate lives in 108.
4. 106 ships arc-coverage report + cast-hierarchy report.
5. 107 ships series-boxset rendering (per-Volume + per-Series outputs)
   when FormatDriver lands.
6. 108 ships series-publish-ready and pov-balance gates.

The 12-axis audit closes on 108's E2E test — which now includes both a
simple novel + a complex novel run.
