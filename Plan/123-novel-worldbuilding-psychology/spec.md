---
spec_id: "123"
slug: novel-worldbuilding-psychology
status: draft
last_updated: 2026-06-09
owner: "@agency"
depends_on: ["102", "105"]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_world*.py
domain: novel / worldbuilding / character-psychology
parent_spec: "101"
mvp-source:
  - "Plan/102-novel-lifecycle-cluster/spec.md §iteration-7 (verb signatures authored there)"
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

## Followup

(Populated when the PR ships.)
