---
spec_id: "141"
slug: chapter-briefing-mode-blocks
status: draft
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["101", "127", "133", "136"]
affects:
  - agency/capabilities/novel/_main.py
  - agency/capabilities/novel/templates/chapter-briefing.md
  - tests/test_novel_chapter_briefing.py
domain: novel / workflow / structure
parent_spec: "101"
mvp-source:
  - "examples/kohaerenz-protokoll/05_welt-sensorik-drafting.md (§9 Kapitel-Briefing-Vorlage 13 Sektionen, §11 Genre-Modus pro Akt)"
  - "examples/kohaerenz-protokoll/01_storyform-und-outline.md (§1 41 Bewegungen, 5 Mode-Blöcke, drei simultane Ebenen)"
---

# Spec 141 — Chapter briefing & narrative-mode blocks

## Why

Between storyform-encoding and prose-drafting the Kohärenz Protokoll runs a
structured **chapter briefing** — a 13-section template (A–M: structural
position, Dramatica-encoding A‖B, POV & voice, prose style, sensorics,
foreshadowing, reader-architecture, conflict-topology, anchor-checks,
adversarial-checks, cross-references, open-questions, pre-draft checklist).
The briefing is "the bridge between storyform-encoding and telling".

The manuscript is also divided into **mode-blocks** — 5+ narrative stances
(Genesis-Prolog / Heldinnenreise / Zyklischer Modus / Heldenreise / Vortex /
Reward / Apotheose / Coda) each carrying three simultaneous values: **Modus**
(narrative stance) · **Storyform-status** (storypoint distribution) ·
**Bridge-frequency** (soft-layering share). Crucially, *mode-changes are NOT
storyform-boundaries* — a distinction the KP flags repeatedly. Plus a
**genre-mode per act** (Philosophical Horror → Literary SF → Technothriller →
chorisches Drama → metaphysischer Klimax → spirituelle Apotheose) with a
"genre-bleed between acts = defect" rule.

Spec 127 (`assemble_scene_brief`) is *scene*-level and graph-driven. The KP
briefing is *chapter*-level, 13-section, encoding-driven — a different
artifact. And nothing today expresses mode-blocks or genre-per-act.

## Done When

- [ ] **`ModeBlock` node** `{novel, label, mode, from_chapter, to_chapter,
      bridge_frequency_target, genre_accent}` — a span of chapters sharing a
      narrative stance. `mode` ∈ `NARRATIVE_MODE` (`linear-introspective` /
      `cyclic-recursive` / `linear-ascending` / `vortex-still` / `choral` /
      `framing`); `genre_accent` is freeform (the §11 per-act genre).
- [ ] **`IN_MODE_BLOCK` edge**: Chapter → ModeBlock (a chapter belongs to one
      block).
- [ ] **Verbs**:
      - `define_mode_block(novel_id, label, mode, from_chapter, to_chapter,
        bridge_frequency_target, genre_accent)` — mints a block.
      - `assign_chapter_to_block(chapter_id, mode_block_id)` — IN_MODE_BLOCK.
      - `mode_block_report(novel_id)` — the §1 table: every block with its
        mode / storyform-status / bridge-target / genre; flags chapters in no
        block (the "unstaged" surface).
      - `check_mode_vs_storyform_boundary(novel_id)` — the KP's load-bearing
        distinction: asserts mode-block boundaries are NOT mislabeled as
        storyform transitions (Spec 136 `StoryformTransition`). A mode-change
        at ch13/14 that is ALSO tagged a storyform transition fails (they are
        orthogonal: the real storyform turn is the Vortex, not the mode edge).
      - `check_genre_bleed(novel_id)` — flags chapters whose drafted genre
        accent (an optional Chapter property) contradicts their block's
        `genre_accent` (the §11 "genre-bleed = defect" rule).
- [ ] **Chapter-briefing template + verbs**:
      - Vendored `templates/chapter-briefing.md` — the 13-section A–M
        template (§9), with `{{placeholder}}` fields the author fills.
      - `render_chapter_briefing(chapter_id)` — composes a briefing: pulls
        the chapter's mode-block, storyform-status (Spec 136 routing),
        POV/voice (Spec 138 alters), sensorics + foreshadowing (Spec 140),
        reveal-architecture (Spec 139), conflict-topology (Spec 138 matrix),
        anchor-checks (Spec 140) — i.e. it *aggregates the whole KP stack into
        one pre-draft document*. Records a `chapter-briefing` Artefact.
      - `briefing_checklist(chapter_id)` — the §9 section-M pre-draft
        checklist as a verb: storyform-status consistent · voice-DNA anchor
        chosen · hot-polarity checked · genesis-echo limit · reveal-layer
        checked · ouroboros-duty (if ch0/1/39/40) · R-rule pre-check.
        Returns `{ready, missing: [str]}`.
- [ ] **scene-writer skill (Spec 130) phase 1 extension**: the assemble phase
      optionally chains `render_chapter_briefing` when a chapter briefing
      hasn't been produced yet — so scene assembly inherits the chapter-level
      decisions.
- [ ] TODO row + drift clean.

## Design notes

- **Briefing aggregates; it doesn't re-implement.** `render_chapter_briefing`
  is a composer over the whole 136–140 stack (like Spec 127 is over the
  scene-level stack). It produces the KP's bridge-document; the sub-specs own
  the underlying data.
- **Mode ≠ storyform is the moat.** The KP warns three times that
  mode-changes (13/14, 26/27) must not be confused with the storyform turn
  (35/36). `check_mode_vs_storyform_boundary` makes that machine-checkable —
  no other surface can express it.
- **Genre-per-act as a soft gate.** Genre-bleed is a defect but the author
  decides; `check_genre_bleed` warns, the editorial pipeline can chain it.
- **Template is vendored + author-overridable** (same pattern as Spec 129
  fragments / Spec 133 structures): the 13-section A–M template ships; a
  project overlay can extend it.

## Open questions

1. Should `render_chapter_briefing` hard-fail when a dependency spec (136–140)
   isn't shipped, or degrade gracefully with a "section pending Spec NNN"
   placeholder? **Recommend**: degrade gracefully (the Spec 127 precedent) —
   placeholders that name the gating spec, so the briefing is useful before
   the whole stack lands.
2. Mode-block overlap — can a chapter be in two blocks (a mode-block AND a
   structure-template beat from Spec 133)? **Recommend**: yes, orthogonal
   layers — IN_MODE_BLOCK (stance) and FULFILS (structure beat, Spec 133) are
   different edges; a chapter carries both.

## Followup

(Populated when the PR ships.)
