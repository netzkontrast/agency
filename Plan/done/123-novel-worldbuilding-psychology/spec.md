---
spec_id: "123"
slug: novel-worldbuilding-psychology
status: shipped
state: done
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["102", "105"]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_world*.py
domain: novel / worldbuilding / character-psychology
parent_spec: "101"
mvp-source:
  - "Plan/inprogress/102-novel-lifecycle-cluster/spec.md §iteration-7 (verb signatures authored there)"
  - "Plan/_research/novel-mvp-source/kohaerenz-decomposition/04-character-and-world/"
  - "agency/capabilities/novel/templates/{character,world}.md (vendored, currently render-only)"
---

# Spec 123 — Worldbuilding + Character Psychology (iteration-7 surface)

## Why

Spec 102's design authored the full iteration-7 surface (World
sub-graph, PsychProfile/Trait, Conflict/Theme, PlantedElement) but
none of it shipped — and the `character-architect` /
`world-bible-architect` walkable skills shipped WITHOUT backing nodes:
their phase outputs vanish into skill-run state instead of becoming
queryable graph entities. This spec gives those skills their ontology.

## Done When

- [ ] **World sub-graph ontology**: `World`, `Culture`, `Religion`,
      `Language`, `MagicSystem`, `WorldAxiom` nodes; `PART_OF_WORLD`
      edge; `severity` enum on WorldAxiom (hard/soft).
- [ ] **Worldbuilding verbs** (per Spec 102 iter-7 signatures):
      `create_world`, `create_culture`, `create_religion`,
      `create_language`, `create_magic_system`, `create_world_axiom`,
      `list_world` (tree transform), `find_axiom_contradictions`
      (CONTRADICTS pairs — feeds a future world-canon gate),
      `link_character_to_world` (edge_type validated against
      BELONGS_TO/INHABITS/WORSHIPS/SPEAKS/WIELDS).
- [ ] **Character psychology layer**: `Character` node (slug, novel,
      archetype, role) + `PsychProfile` (lens enum: big-five /
      enneagram / ifs / jung) + `Trait` nodes;
      `generate_psych_profile(character, lens)` +
      `select_psych_framework(novel, genre)` (genre→framework table as
      documented tunable) + `validate_dramatica_mapping(character)`
      (archetype↔trait contradiction warnings — reads the vendored
      ontology's 8 archetypes via Spec 120's `_resolve_term`).
- [ ] **Conflict + Theme + foreshadowing**: `Conflict` (scope/type/
      intensity enums) + `Theme` (motif_words, central) +
      `PlantedElement` (status enum: planted/partially-paid/paid/
      orphaned); verbs `track_conflict`, `conflict_density_report`,
      `declare_theme`, `check_thematic_motif_distribution`,
      `plant_element`, `mark_paid_off`, `orphaned_foreshadowing_report`.
- [ ] **Skill rewiring**: `character-architect` + `world-bible-architect`
      phases bind to the new effect verbs (phase-bound verbs EXECUTE) —
      walk output becomes graph state.
- [ ] `developmental_gate` (Spec 122) extends with conflict-present +
      orphaned-foreshadowing predicates once both specs land.
- [ ] TODO.md row updated.

## Design notes

- This is the largest remaining ontology delta (~10 nodes). Land in 2
  slices: world sub-graph first, psychology + foreshadowing second.
- Big Five stored as dict {O,C,E,A,N: 0-100}; enneagram as "1".."9"
  + wings — open string with format validation, not a 27-value enum.

## Open questions

1. Are Conflict/Theme novel-scoped or world-scoped? (Recommend:
   novel-scoped; a shared world spans novels but themes are per-work.)
2. `find_axiom_contradictions` — decidable (keyword negation match) or
   judgement (skill)? (Recommend: ship decidable v1 flagging axiom
   pairs sharing motif words with negation markers; judgement pass via
   `thinking.red_team` xcap.)

## Followup — Implementation Status (2026-06-10)

**Done (Slice 1 — World sub-graph):**
- 6 new ontology nodes shipped: `World`, `Culture`, `Religion`,
  `Language`, `MagicSystem`, `WorldAxiom`.
- 2 new edges: `PART_OF_WORLD` (Culture/Religion/Language/MagicSystem/Axiom
  → World); `CONTRADICTS` (WorldAxiom ↔ WorldAxiom, written by
  `find_axiom_contradictions`); plus 5 character-to-world relationship
  edges (`BELONGS_TO`, `INHABITS`, `WORSHIPS`, `SPEAKS`, `WIELDS`).
- `WORLD_AXIOM_SEVERITY = {"hard", "soft"}` enum on WorldAxiom.severity.
- `_CHARACTER_WORLD_EDGES` whitelist gates `link_character_to_world`.
- **9 verbs shipped**: `create_world`, `create_culture`, `create_religion`,
  `create_language`, `create_magic_system`, `create_world_axiom`,
  `list_world` (tree transform using `ctx.neighbors` PART_OF_WORLD per
  Spec 125), `find_axiom_contradictions` (decidable scan: 2+ shared
  motif words + exactly-one-side negation marker; writes CONTRADICTS
  edges so the relationship is queryable), `link_character_to_world`
  (edge-kind whitelist).
- `find_axiom_contradictions` Open Q2 resolved: shipped decidable v1
  (negation-XOR + motif-word overlap). Judgement pass via
  `thinking.red_team` xcap is documented as future work.

**Still (Slice 2 — deferred):**
- **Character psychology layer**: `Character`/`PsychProfile`/`Trait`
  nodes; `generate_psych_profile(character, lens)`;
  `select_psych_framework(novel, genre)`;
  `validate_dramatica_mapping(character)` reading the 8 archetypes via
  Spec 120's `_resolve_term`.
- **Conflict + Theme + foreshadowing**: `Conflict`/`Theme`/`PlantedElement`
  nodes; `track_conflict`, `conflict_density_report`, `declare_theme`,
  `check_thematic_motif_distribution`, `plant_element`, `mark_paid_off`,
  `orphaned_foreshadowing_report`.
- **Skill rewiring**: `character-architect` + `world-bible-architect`
  phases bind to the Slice 1+2 effect verbs once Slice 2 lands.
- **Cross-spec hook**: `developmental_gate` (Spec 122) extends with
  conflict-present + orphaned-foreshadowing predicates after Slice 2.

**Open Q resolutions:** Q1 — novel-scoped Conflict/Theme (per spec
recommendation); shared World spans novels. Q2 — decidable v1 shipped
(motif-words + negation-XOR); judgement pass deferred.

**Test:** 14 new tests (`tests/test_novel_worldbuilding.py`) — node /
enum / edge / verb registration, create_world + 4 children with
PART_OF_WORLD edges, unknown-world rejection, axiom severity enum
validation, `list_world` tree grouping by label, contradiction detection
(negation-XOR true positive + clean true negative), edge-kind whitelist
enforcement, character-world edge round-trip. 249 across novel/naming/
install green; drift clean.
