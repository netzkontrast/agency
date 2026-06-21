---
spec_id: "133"
slug: story-structure-templates
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["101", "103", "120"]
affects:
  - agency/capabilities/novel/_main.py
  - agency/capabilities/novel/data/structures/*.json
  - tests/test_novel_structure_templates.py
domain: novel / structure / pacing
parent_spec: "101"
mvp-source:
  - "Save the Cat (Snyder) — 15-beat sheet, the dominant commercial-fiction structure"
  - "Three-Act / Hero's Journey / Story Circle / Snowflake — public domain structures, taught in every craft book"
  - "User brainstorm 2026-06-10 — pacing complement to Dramatica's meaning engine"
---

# Spec 133 — Story structure templates (pacing layer)

## Why

Storyform (Dramatica, Spec 103/120) covers the **what** of meaning —
which character archetype, which throughline, which problem element.
What it doesn't cover is **pacing** — where the inciting incident lands,
when the midpoint flips, how the third act compresses. Authors think
in named beats ("Save the Cat" page 25 catalyst, "Three-Act" act break)
when planning manuscripts; agency today has no surface for it.

Without this, the scene-writer skill (Spec 130) can compose great
sentences but the manuscript drifts pace-wise — a known failure mode
the editorial-pipeline (Spec 122) catches *after* it happened, not
*before*.

## Done When

- [ ] **Vendored templates** in
      `agency/capabilities/novel/data/structures/`:
      `save-the-cat.json` (15-beat), `three-act.json` (3-act + midpoint
      + climax = 6 beats), `heros-journey.json` (12-beat Campbell),
      `story-circle.json` (8-beat Harmon), `snowflake.json` (Ingermanson
      — 1-sentence → 1-paragraph → 1-page expansion).
      Each entry: `{template_id, name, source, beats: [{slug, name,
      position: 0.0-1.0, prompt}]}` where `position` is the canonical
      manuscript fraction (0.0 = page 1, 1.0 = last page) and `prompt`
      is the author-facing question per beat ("What promise opens the
      story?").
- [ ] **Ontology additions**:
      - `StructureTemplate` node (registered by id; no graph state — pure
        lookup)
      - `BeatExpectation` node `{novel_id, template_id, beat_slug,
        target_position, scene_id?}` — minted when the author applies a
        template; `scene_id` is filled when the author maps the
        manuscript scene that fulfils the beat
      - `FULFILS` edge: Scene → BeatExpectation
- [ ] **6 verbs on `novel` cap**:
      - `list_structure_templates() -> [{template_id, name, source,
        beat_count}]` — discovery
      - `get_structure_template(template_id) -> full template body` —
        Read with all beats + prompts
      - `apply_structure(novel_id, template_id)` — mints
        `BeatExpectation` nodes for every beat in the template;
        idempotent on `(novel_id, template_id)` (re-application
        overwrites the un-anchored beats, preserves anchored ones)
      - `anchor_beat(novel_id, beat_slug, scene_id)` — maps a scene to a
        beat (mints `FULFILS` edge + updates `BeatExpectation.scene_id`)
      - `check_structure_coverage(novel_id) ->
        {anchored, unanchored: [{beat_slug, name, target_position}]}` —
        the author's checklist
      - `structure_position_report(novel_id) -> {beats: [{beat_slug,
        target_position, actual_position}]}` — for each anchored beat,
        computes `actual_position` from the scene's chapter+order vs
        total manuscript length; flags beats whose `|actual - target|
        > 0.10` as `out_of_position`
- [ ] **`develop.skill_walk("storyform-build")` extension** (Spec 120):
      after the storyform composite passes, an OPTIONAL chained
      template-pick phase — author can `apply_structure` without leaving
      the walk.
- [ ] **Lint rule**: a Novel with `status="drafting"` and NO
      `BeatExpectation` triggers a soft warning in
      `manuscript_coherence_check` ("no structure template applied;
      pacing is unmeasured"). The author can ignore — soft severity.
- [ ] TODO row + drift clean.

## Design notes

- **Templates are data**, not code. JSON-loaded; future authors can add
  templates in `.agency/structure-templates-overlay.yaml` (same pattern
  as Spec 129 fragments).
- **Position is a fraction, not page count** — manuscripts have no
  fixed pages, so anchoring by "chapter X of N" + relative position is
  the only portable measure.
- **One template per novel** — multi-template overlays (Save the Cat +
  Hero's Journey on the same manuscript) is a stretch; for v1 the author
  picks one. Templates can be SWITCHED — `apply_structure` is
  idempotent so switching preserves manuscript anchors that share beat
  slugs across templates.
- **Storyform-coexistence is by design**: Dramatica + structure both
  fire on the same manuscript; they answer different questions.

## Open questions

1. **Should `BeatExpectation.prompt` ship as the per-entry guidance
   blob, or be derived from the template body on read?**
   *Recommend*: blob it onto the node at `apply_structure` time so a
   later template edit doesn't retroactively rewrite committed
   expectations.
2. **Save the Cat is trademarked**; we ship the *structure*, not the
   prose. Beat names ("Opening Image", "Theme Stated", "Catalyst", etc.)
   are widely taught and not protected; the bundled `prompt` field stays
   in our voice. Verify with a quick license note in the JSON.
3. **`actual_position` computation**: use chapter midpoint (chapter N
   of 30 → 0.5 if midpoint chapter) OR cumulative word count to that
   scene / total words? *Recommend*: cumulative word count when
   available (chapters have body); chapter midpoint when not.

## Followup

(Populated when the PR ships.)
