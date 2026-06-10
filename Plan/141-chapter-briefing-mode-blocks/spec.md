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

## Schema

```text
# New enum
NARRATIVE_MODE = {
  "linear-introspective",   # Akt I Heldinnenreise (Kael)
  "cyclic-recursive",       # Akt II Zyklischer Modus
  "linear-ascending",       # Akt III Heldenreise (AEGIS)
  "vortex-still",           # Vortex / Reward
  "choral",                 # Apotheose, multi-voice
  "framing",                # Genesis-Prolog, Coda
}

# New node
ModeBlock {
  novel:                   str
  label:                   str   # "Akt I Heldinnenreise", "Vortex 1"
  mode:                    str   # ∈ NARRATIVE_MODE
  from_chapter:            int
  to_chapter:              int
  bridge_frequency_target: float # 0.10 / 0.25 / 0.40 / 1.00
  genre_accent:            str   # freeform: "Philosophical Horror" / "Literary SF" / …
}

# Extends existing Chapter node (additive)
Chapter.genre_accent_drafted: str   # optional — checked by check_genre_bleed

# New edge
IN_MODE_BLOCK : Chapter --→ ModeBlock     (cardinality N:1)
```

## Verb signatures

```python
def define_mode_block(
    novel_id: str,
    label: str,
    mode: str,
    from_chapter: int,
    to_chapter: int,
    bridge_frequency_target: float = 0.0,
    genre_accent: str = "",
) -> dict:
    """Returns: {mode_block_id, label, mode, from_chapter, to_chapter,
                 bridge_frequency_target, genre_accent}
    Raises on unknown mode; rejects from_chapter > to_chapter; rejects
    overlap with an existing block in the same novel.
    """

def assign_chapter_to_block(chapter_id: str, mode_block_id: str) -> dict:
    """Mints IN_MODE_BLOCK. A chapter has exactly one mode-block (rebind
    replaces). Returns: {chapter_id, mode_block_id, replaced: <prev-or-empty>}"""

def mode_block_report(novel_id: str) -> dict:
    """The §1 table.
    Returns: {
      blocks: [{label, mode, from_chapter, to_chapter,
                bridge_frequency_target, genre_accent,
                chapter_count: int, storyform_distribution: {role: int}}…],
      unstaged_chapters: [{chapter_id, chapter_number, title}…],
      total_chapters: int,
    }
    """

def check_mode_vs_storyform_boundary(novel_id: str) -> dict:
    """The KP's load-bearing distinction. A mode-block edge (transition between
    blocks) MUST NOT coincide with a Spec 136 StoryformTransition at the same
    chapter — those are orthogonal layers.
    Returns: {
      passed: bool,
      collisions: [{at_chapter, mode_from, mode_to,
                    storyform_from_role, storyform_to_role,
                    verdict: "mode-mislabeled-as-storyform"}…],
      block_edges: [{at_chapter, mode_from, mode_to}…],
      storyform_edges: [{at_chapter, kind}…],
    }
    """

def check_genre_bleed(novel_id: str) -> dict:
    """Chapter.genre_accent_drafted must equal its ModeBlock.genre_accent
    (or be empty). Mismatch = §11 "genre-bleed = defect".
    Returns: {
      passed: bool,
      bleeds: [{chapter_id, chapter_number,
                drafted: str, expected: str, block_label: str}…],
    }
    """

def render_chapter_briefing(
    chapter_id: str,
    template_path: str = "novel/templates/chapter-briefing.md",
) -> dict:
    """Composes the 13-section briefing by aggregating the whole stack.
    Returns: {
      briefing_id:   str,            # the Artefact node
      chapter_id:    str,
      sections: {
        "A": {filled: bool, body: str, source: "spec-141"},
        "B": {filled: bool, body: str, source: "spec-136"},  # storyform encoding
        "C": {filled: bool, body: str, source: "spec-138"},  # POV & voice
        "D": {filled: bool, body: str, source: "spec-134"},  # prose style
        "E": {filled: bool, body: str, source: "spec-140"},  # sensorics
        "F": {filled: bool, body: str, source: "spec-140"},  # foreshadowing
        "G": {filled: bool, body: str, source: "spec-139"},  # reader-architecture
        "H": {filled: bool, body: str, source: "spec-138"},  # conflict-topology
        "I": {filled: bool, body: str, source: "spec-140"},  # anchor-checks
        "J": {filled: bool, body: str, source: "spec-122"},  # adversarial-checks
        "K": {filled: bool, body: str, source: "spec-133"},  # cross-references
        "L": {filled: bool, body: str, source: "spec-137"},  # open-questions ([L])
        "M": {filled: bool, body: str, source: "spec-141"},  # pre-draft checklist
      },
      missing_specs: [str…],   # specs not yet shipped — degraded gracefully
      template_used: str,
    }
    Degrades gracefully: when a dep spec isn't shipped, the section body is
    `"<pending Spec NNN — see briefing template §X>"` rather than failing.
    """

def briefing_checklist(chapter_id: str) -> dict:
    """The §9 section-M pre-draft checklist as a verb.
    Returns: {
      ready: bool,
      items: [
        {check: "storyform-status-consistent",   ok: bool, detail: str},
        {check: "voice-dna-anchor-chosen",       ok: bool, detail: str},
        {check: "hot-polarity-checked",          ok: bool, detail: str},
        {check: "genesis-echo-limit",            ok: bool, detail: str},
        {check: "reveal-layer-checked",          ok: bool, detail: str},
        {check: "ouroboros-duty",                ok: bool, detail: str},  # ch 0/1/39/40 only
        {check: "r-rule-pre-check",              ok: bool, detail: str},
      ],
      missing: [str…],
    }
    """
```

## Vendored 13-section template

`agency/capabilities/novel/templates/chapter-briefing.md` — the A–M template
ships in this PR; sections embed `{{placeholders}}` and reference the
sub-specs that aggregate into them. Author overlay via project's
`.agency/chapter-briefing-overlay.md` (same vendored-with-overlay pattern as
Spec 129 fragments / Spec 133 structures).

## Scene-writer (Spec 130) phase-1 extension

```python
# Today (Spec 130 phase 1 — assemble):
brief = assemble_scene_brief(scene_id, …)

# After Spec 141 ships:
chapter = get_chapter_of_scene(scene_id)
if not chapter.has_briefing:                          # NEW
    chapter_briefing = render_chapter_briefing(chapter.id)   # NEW
    # chapter-level decisions cascade into scene assemble
brief = assemble_scene_brief(scene_id, …, chapter_briefing=chapter_briefing)
```

Backwards compatible: when `chapter_briefing` is absent the scene-brief
behaves as today.

## Test scaffold

```text
tests/test_novel_chapter_briefing.py  (target ≥ 22 tests)
  test_narrative_mode_enum_registered
  test_define_mode_block_happy_path
  test_define_mode_block_rejects_unknown_mode
  test_define_mode_block_rejects_inverse_chapter_range
  test_define_mode_block_rejects_overlap
  test_assign_chapter_to_block_mints_IN_MODE_BLOCK
  test_assign_chapter_to_block_rebind_replaces
  test_mode_block_report_lists_unstaged
  test_mode_block_report_chapter_count_per_block
  test_check_mode_vs_storyform_boundary_passes_when_orthogonal
  test_check_mode_vs_storyform_boundary_flags_collision
  test_check_genre_bleed_passes_clean
  test_check_genre_bleed_flags_drafted_mismatch
  test_render_chapter_briefing_produces_artefact
  test_render_chapter_briefing_aggregates_all_13_sections
  test_render_chapter_briefing_degrades_for_missing_specs
  test_render_chapter_briefing_records_template_used
  test_briefing_checklist_returns_seven_items
  test_briefing_checklist_ouroboros_only_for_boundary_chapters
  test_briefing_checklist_ready_when_all_ok
  test_briefing_checklist_lists_missing
  test_scene_writer_phase1_chains_render_when_briefing_absent
  test_scene_writer_phase1_skips_render_when_briefing_present
```

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
3. ModeBlock overlap WITHIN this spec — a chapter belonging to two ModeBlocks?
   **Recommend**: no — `IN_MODE_BLOCK` is N:1; rebind replaces. Mode is a
   single stance per chapter.
4. Should `check_mode_vs_storyform_boundary` ALSO flag the inverse (a
   storyform-transition with NO mode-change at the same chapter)?
   **Recommend**: no — the inverse is fine (the Vortex turns storyform without
   turning mode in the same chapter); only the false-equation direction is
   the documented KP defect.

## Followup

(Populated when the PR ships.)
