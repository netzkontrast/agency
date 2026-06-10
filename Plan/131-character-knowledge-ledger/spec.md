---
spec_id: "131"
slug: character-knowledge-ledger
status: draft
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["101", "123", "128"]
affects:
  - agency/capabilities/novel/_main.py
  - agency/capabilities/prompt/_main.py
  - tests/test_novel_character_knowledge.py
domain: novel / character / continuity
parent_spec: "101"
mvp-source:
  - "User brainstorm 2026-06-10"
  - "Plan/127/spec.md _pov_card future enrichment"
---

# Spec 131 — Character-knowledge ledger

## Why

Continuity bugs in long-form prose almost always trace to "the POV
character knows something they shouldn't know yet." Agency has
characters (Spec 123 Slice 2 adds Character nodes) and scenes; what's
missing is the ledger of *facts known by each character at each
narrative beat*. Spec 127's `_pov_card` placeholder explicitly names
this gap.

## Done When

- [ ] **`KnownFact` node** — `{character_id, fact, learned_in_scene}`.
      `fact` is freeform; structure comes from the author's care, not
      the schema.
- [ ] **`KNOWS` edge** — Character → KnownFact (so a character's known
      set is one `ctx.neighbors(character_id, "KNOWS")` call).
- [ ] **`LEARNED_IN` edge** — KnownFact → Scene (the disclosure point).
- [ ] **Verbs**:
      - `record_character_learns(character_id, fact, scene_id)` — mints
        KnownFact + KNOWS + LEARNED_IN edges.
      - `what_does_X_know_as_of(character_id, scene_id)` — walks
        KnownFacts whose LEARNED_IN scene `when_narrative` ≤ the target
        scene's `when_narrative` (uses Spec 128 NarrativeBeat
        ordering).
      - `flag_anachronistic_reference(scene_id, character_id, fact_text)`
        — checks if the character KNOWS the fact yet; returns
        `{anachronism, expected_learned_in}` when the scene's narrative
        position precedes the LEARNED_IN.
- [ ] **`prompt.assemble_scene_brief` upgrade** — `_pov_card` includes
      a "POV knows" subsection listing facts learned through THIS
      scene's narrative position. The negative ("POV does NOT know X")
      is harder; defer to a future spec.
- [ ] Test fixture: 3-scene mini-novel where Character A learns fact in
      scene 2; assemble_scene_brief for scene 1 lists nothing in
      "POV knows"; scene 2+ lists the fact.
- [ ] TODO row.

## Design notes

- `fact` is freeform string; the ledger is metadata, not a semantic
  graph. The author writes "knows the captain is bribed" — no
  proposition parsing.
- The "POV does NOT know X" check requires the author to enumerate
  facts they intentionally hide; out of v1 scope.

## Open questions

1. Forgetting/unlearning — relevant for trauma/amnesia plots. **Recommend**:
   defer; add a `FORGOT` edge in a future slice when an author asks for
   it. Most stories monotonically accumulate knowledge.
2. Should KnownFact participate in the embedding store (Spec 005 / 045
   reflections)? **Recommend**: no — the ledger is small and
   author-curated; embedding indexing would be premature.

## Followup

(Populated when the PR ships.)
