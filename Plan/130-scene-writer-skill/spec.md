---
spec_id: "130"
slug: scene-writer-skill
status: shipped
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

## Followup — Implementation Status (2026-06-10)

**Done (Slice 1):**
- `scene-writer` 5-phase walkable skill registered on novel ontology
  (`SCENE_WRITER_SKILL`):
  1. **assemble** → binds to `prompt.assemble_scene_brief` (Spec 127)
  2. **validate-constraints** → no bound verb yet (the brief's
     `token_count` + `truncated` flags carry the validation; phase
     output is the gate)
  3. **generate** → no driver binding yet (FakeTextDriver + production
     TextDriver are Slice 2 territory, gated on Spec 005)
  4. **check** → binds to 4 verbs: `novel.check_filter_words`,
     `novel.check_dialogue_attribution`, `novel.check_show_dont_tell`,
     `novel.novel_coherence_check`
  5. **integrate** (HARD GATE) → binds to new `novel.integrate_scene_body`
- `novel.integrate_scene_body(scene_id, body)` shipped — promotes a
  draft body onto the Scene node via `ctx.memory.update`, records
  `Artefact(kind="scene-integration", scene_id, bytes)` with SERVES +
  PRODUCES edges. NOT_FOUND on unknown scene_id.
- All 5 phase names + verb bindings + hard gate on phase 5 visible
  through `e.ontology.skills["scene-writer"]`.

**Still (Slice 2 — gated on Spec 005):**
- **FakeTextDriver** fixture for phase 3 (generate) — returns `"[stub
  scene body]"` deterministically so the walk is binary-free + LLM-free
  in CI. Production TextDriver Protocol is Spec 005's territory.
- **Phase 2 validation verb** — could bind to a new `validate_brief_shape`
  effect verb that gates on the brief's `token_count > 4000` or
  `len(truncated) > 0`. Deferred — current walks rely on the orchestrator
  to read the brief shape between phases.
- **Auto-update LEARNED_IN ledger** on phase 5 — Slice 2 will extend
  `integrate_scene_body` to call `novel.record_character_learns` for any
  facts the scene body introduces (parsed from the generate phase's
  metadata). Slice 1 just writes the body.

**Open Q resolutions:**
- Q1: per-scene granularity (Slice 1 default); a future `chapter-writer`
  skill composes scene-writer N times.
- Q2: `SceneBrief.draft_body` transient property is the carry between
  phase 3 and phase 5 (when generate ships); phase 5 promotes to
  `Scene.body` on confirmation.

**Test:** 9 new tests (`tests/test_novel_scene_writer_skill.py`) —
skill registration, 5-phase shape, phase 1 binds to
`prompt.assemble_scene_brief`, phase 4 chains 4 prose/storyform checks,
phase 5 is hard gate + binds to `integrate_scene_body`,
integrate_scene_body writes body + records Artefact + rejects unknown
scene + verb registered. 303 across novel/prompt/naming/install green;
drift clean.

**Closes the dynamic-prompt depth wave**: with 128 (story-time
graph), 129 (Dramatica fragments), 131 (character knowledge), 132
(codex entities) shipped and now this integration layer, the wave is
complete at Slice 1. Spec 127's `assemble_scene_brief` now has all 7
sections grounded in real graph queries (storyform via 129, continuity
via 128, pov_card via 131, world_rules via 132; pov + voice + scene_cast
direct from Scene properties). The scene-writer skill ties them into a
walkable loop.
