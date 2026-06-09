---
spec_id: "122"
slug: novel-editorial-pipeline
status: draft
last_updated: 2026-06-09
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

## Followup

(Populated when the PR ships.)
