---
spec_id: "130"
slug: scene-writer-skill
status: draft
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["120", "127", "128", "129", "131"]
affects:
  - agency/capabilities/novel/_main.py
  - agency/capabilities/develop/_main.py
  - tests/test_novel_scene_writer_skill.py
domain: novel / workflow / walkable-skill
parent_spec: "101"
mvp-source:
  - "User brainstorm 2026-06-10 — scene-writer 5-phase skill"
---

# Spec 130 — Scene-writer walkable skill

## Why

127 + 128 + 129 + 131 + 132 each ship a piece of the dynamic prompt
machinery. The author still has to orchestrate: assemble → validate →
generate → check → integrate. A walkable skill makes the whole loop one
operation (`develop.skill_walk("scene-writer", scene_id=...)`).

## Done When

- [ ] **`scene-writer` skill** registered on novel ontology with 5
      phases, verb-bound where verbs exist:
      1. **assemble** — binds to `prompt.assemble_scene_brief`. Produces
         the SceneBrief Artefact.
      2. **validate-constraints** — checks brief is within
         `section_budget` and `max_tokens` caps (already enforced) +
         POV character voice constraints (from Spec 123 PsychProfile
         when shipped, otherwise pass-through).
      3. **generate** — driver-bound to a future TextDriver (Spec 005
         territory); FakeTextDriver returns a stub body so the walk
         is testable. Produces the scene body string.
      4. **check** — chains:
         a. `novel.check_filter_words`
         b. `novel.check_dialogue_attribution`
         c. `novel.check_show_dont_tell`
         d. `novel.novel_coherence_check` on the storyform (if
            the scene's chapter has a Storyform body).
      5. **integrate** (HARD GATE) — writes the scene body back to the
         Scene node; updates `LEARNED_IN` ledger (Spec 131) for any
         facts the scene introduces; rolls forward `NarrativeBeat`
         (Spec 128). Hard gate halts until orchestrator confirms.
- [ ] **5 walk-phase tests** — each phase fires its bound verb; phase 4
      aggregates check verdicts; phase 5 short-circuits on un-confirmed
      gate.
- [ ] Test fixture uses FakeTextDriver to keep CI binary-free.
- [ ] TODO row.

## Design notes

- This is the integration spec — almost no new verbs; the work is in
  the phase bindings + the FakeTextDriver fixture.
- The TextDriver Protocol is OUT of scope here (Spec 005's territory);
  Slice 1 ships a noop FakeTextDriver returning `"[stub scene body]"`.
  Production TextDriver lands later.

## Open questions

1. Per-scene generation or per-chapter? **Recommend**: per-scene (this
   skill); a future `chapter-writer` skill composes scene-writer N times.
2. Where does the GENERATED scene body live before phase 5? **Recommend**:
   in `SceneBrief.draft_body` (a transient property on the Artefact);
   phase 5 promotes to Scene.body on confirmation.

## Followup

(Populated when the PR ships.)
