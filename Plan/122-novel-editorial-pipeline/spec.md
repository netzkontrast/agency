---
spec_id: "122"
slug: novel-editorial-pipeline
status: shipped
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["104", "108"]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_prose*.py
domain: novel / prose / editorial
parent_spec: "101"
mvp-source:
  - "agency/capabilities/novel/data/reference/skills-catalogue.md (32-skill parity table)"
  - "Plan/_research/novel-mvp-source/legacy-skills/ (editorial SKILL.md sources)"
  - "agency/capabilities/music/_main.py (lyric gates as reference pattern)"
---

# Spec 122 — Novel Editorial Pipeline (remaining prose verbs + 3 stage gates)

## Why

Spec 104 shipped 7 of 12 prose verbs. The missing 5 are the
*chapter-spanning* checks (consistency across bodies, not within one
body) — and the 3 editorial-stage gates that compose them are how a
manuscript actually moves through developmental → line → copy editing.
The skills-catalogue's 28 editorial skills assume these gates exist.

## Done When

- [ ] **5 remaining prose verbs ship** (all transforms, driver-free):
      - `check_voice_consistency(bodies)` — per-chapter voice signature
        (avg sentence length, filter-word density, attribution style)
        + outlier detection across chapters.
      - `check_pov_consistency(novel_id)` — Scene.pov uniformity per
        chapter; flags mid-chapter POV breaks (reads Scene nodes).
      - `check_continuity(novel_id)` — proper-noun registry across
        chapters via `scan_proper_nouns`; flags single-chapter-only
        names (likely typos) + spelling-variant pairs (Lara/Laura).
      - `check_sensitivity(body)` — extends `check_content_warnings`
        with a documented sensitivity-topic lexicon; advisory severity.
      - `chapter_report_full(chapter_id)` — act-role aggregate: runs
        every prose check over ONE chapter, produces `chapter-report`
        artefact (the editorial dashboard for a single chapter).
- [ ] **3 composite editorial gates** (effects, mirror music's
      lyric-gate pattern):
      - `developmental_gate(novel_id)` — structure-level: storyform
        coherent (delegates to Spec 120's composite when shipped, else
        the 3 live checks) + chapter contiguity + conflict present.
      - `line_gate(novel_id)` — prose-level: filter-word density +
        show-don't-tell + dialogue attribution within thresholds on
        EVERY chapter.
      - `copy_gate(novel_id)` — surface-level: continuity + content
        warnings declared + readability in genre band.
- [ ] **2 walkable skills**: `developmental-editor` (5-phase, hard
      sign-off) + `line-editor` (4-phase) — phases bind to the gate
      verbs (a phase bound to a verb EXECUTES, per skills doctrine).
- [ ] **Exact-severity discipline**: advisory checks (sensitivity) never
      block gates; WARN surfaces in the report.
- [ ] TODO.md row updated; Spec 104 "Still" carve-outs pointed here.

## Open questions

1. Voice-signature outlier threshold — z-score over chapters or fixed
   band? (Recommend: z > 2.0 as documented tunable.)
2. Genre readability bands for `copy_gate` — ship a small documented
   table (literary 60-70, thriller 70-80, YA 80-90 Flesch)?

## Followup — Implementation Status (2026-06-10)

**Done:**
- **5 chapter-spanning prose verbs** shipped on `novel` cap:
  - `check_voice_consistency(bodies, z_threshold=2.0)` — per-body 3-feature
    voice signature (avg sentence length, filter density, flowery-attribution
    density); z-score outlier detection (default 2.0 — Open Q1 resolved
    as the documented tunable).
  - `check_pov_consistency(novel_id)` — uses `ctx.neighbors` to walk
    Chapter → SCENE_OF; flags chapters with > 1 distinct POV.
  - `check_continuity(novel_id)` — proper-noun registry via internal
    helper; flags single-chapter names (likely typos) + close-distance
    spelling pairs (Levenshtein ≤ 2 for strings ≥ 4 chars).
  - `check_sensitivity(body)` — extends content-warnings with mental-health
    / identity / trauma lexicon; **always passes** (advisory severity per
    spec's exact-severity discipline).
  - `chapter_report_full(chapter_id)` — runs every prose check over one
    chapter; records `Artefact(kind="chapter-report")` with SERVES edge.
- **3 composite editorial-stage gates** shipped:
  - `developmental_gate(novel_id)` — chapter contiguity + storyform
    presence; structure-level pass condition.
  - `line_gate(novel_id)` — filter / show-don't-tell / dialogue
    attribution clean on EVERY chapter + POV consistent across scenes.
  - `copy_gate(novel_id)` — continuity registry clean + content_warnings
    declared on the Novel node; readability warnings are advisory only.
- **2 walkable skills** shipped: `developmental-editor` (5-phase, hard
  sign-off; phase 3 binds to `developmental_gate`) + `line-editor`
  (4-phase; phase 3 binds to `line_gate`). Phases bind to real verbs so
  walking the skill EXECUTES the editorial pass per Spec 080 doctrine.
- `_SENSITIVITY_LEXICON` module-level dict for the advisory check;
  `_levenshtein` stdlib-only helper for the continuity close-pair scan.

**Open Q resolutions:** Q1 — `z > 2.0` as documented tunable (test
suite uses 1.5 for small-sample validation). Q2 — readability bands
deferred to a follow-up; current `copy_gate` emits advisory warnings
outside 50-90 Flesch (genre-agnostic) and never blocks on readability.

**Test:** 17 new tests (`tests/test_novel_editorial_pipeline.py`) —
verb + skill registration, phase-gate bindings, voice consistency
pass/outlier, POV uniform/mixed, continuity clean/single-chapter-name/
close-spelling-pair, sensitivity advisory warnings, chapter report
aggregation + Artefact, developmental gate block-on-missing-storyform +
pass-with-substrate, line gate clean-prose, copy gate
block-on-undeclared-warnings. 252 across novel/naming/install green;
drift clean; surface_size accept-warn already documents the novel cap.

**Hooks Spec 120:** `developmental-editor` skill phase 2 binds to
`novel_coherence_check` (the storyform composite from Spec 120 —
shipped); walking the skill drives storyform → developmental → line →
copy in order.
