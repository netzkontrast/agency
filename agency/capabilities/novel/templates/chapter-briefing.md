---
type: novel.chapter-briefing
author_slug: "{{author_slug}}"
work_slug: "{{work_slug}}"
chapter_id: "{{chapter_id}}"
chapter_number: "{{chapter_number}}"
chapter_title: "{{chapter_title}}"
created: "{{created}}"
status: pre-draft
template_version: 1
---

<!-- AGENT: Render this chapter-briefing.md per chapter via `novel.render_chapter_briefing` (Spec 141). Fill the 13 sections (A–M) by aggregating the 122 / 133 / 134 / 136 / 137 / 138 / 139 / 140 stack; sections gated by an unshipped dependency render `<pending Spec NNN — see §X>`. Project overlay: `.agency/chapter-briefing-overlay.md`. -->

<!-- Spec 141 — 13-section chapter-briefing template (A–M).
     Vendored. Project may override via .agency/chapter-briefing-overlay.md
     (same vendored-with-overlay pattern as Spec 129 fragments / Spec 133
     structures). Aggregates Specs 122 / 133 / 134 / 136 / 137 / 138 / 139 /
     140. Sections render `<pending Spec NNN — see §X>` when a dep isn't shipped. -->

# Chapter Briefing — {{chapter_number}}: {{chapter_title}}

## A. Structural position
<!-- Source: Spec 141 — ModeBlock + Spec 133 structure beat -->
- Mode-block: `{{mode_block_label}}` ({{mode_block_mode}})
- Chapter range: `{{from_chapter}}–{{to_chapter}}`
- Bridge-frequency target: `{{bridge_frequency_target}}`
- Genre accent: `{{genre_accent}}`
- Structure beat (Spec 133): `{{structure_beat}}`

## B. Dramatica encoding (A ‖ B)
<!-- Source: Spec 136 dual-storyform routing for this chapter -->
- Routing mode: `{{route_mode}}` (hard | soft)
- Storyform A status: `{{storyform_a_status}}`
- Storyform B status: `{{storyform_b_status}}`
- Active signposts: A=`{{signpost_a}}` · B=`{{signpost_b}}`
- Any active StoryformTransition this chapter? `{{transition_kind_or_none}}`

## C. POV & voice
<!-- Source: Spec 138 alters + Spec 134 voice-DNA -->
- POV alter (fronting): `{{pov_alter_name}}` ({{pov_alter_category}})
- Voice profile: `{{voice_profile_slug}}`
- Co-fronting alters (warn if max-pair): `{{cofronting}}`
- Speakers in scene (Spec 134): `{{speakers}}`

## D. Prose style
<!-- Source: Spec 134 voice + Spec 104 prose-engine knobs -->
- Register: `{{register}}`
- Tense / aspect: `{{tense}}`
- Sentence-length target: `{{sent_len_target}}`
- Filter-word budget (Spec 122): `{{filter_word_budget}}`
- Show-don't-tell pressure: `{{stdt_pressure}}`

## E. Sensorics
<!-- Source: Spec 140 motif registry + Spec 132 codex (sensorics) -->
- Active motifs (≤ 1 echo per scene): `{{motif_slugs}}`
- Polarity locks (R-5 hot-polarity): `{{polarity_locks}}`
- Kernwelt-Schicht (KP-specific): `{{kernwelt}}`
- Somatik tags: `{{somatik}}`

## F. Foreshadowing
<!-- Source: Spec 140 Anchor PLANTS/PAYS_OFF -->
- Anchors planted here: `{{anchors_planted}}`
- Anchors paid off here: `{{anchors_paid_off}}`
- Open anchors (planted, unpaid): `{{open_anchors}}`

## G. Reader-architecture
<!-- Source: Spec 139 reveal-rules + Leerstellen -->
- Reader tier reveals due this chapter: `{{reader_reveals}}`
- POV tier reveals: `{{pov_reveals}}`
- Antagonist tier reveals: `{{antagonist_reveals}}`
- Veil status (`check_veil`): `{{veil_status}}`
- Planned Leerstellen: `{{planned_gaps}}`

## H. Conflict topology
<!-- Source: Spec 138 PHOBIA_OF matrix + Spec 131 character-knowledge -->
- Active phobia-pairs in this chapter: `{{active_phobia_pairs}}`
- Max-intensity warnings: `{{max_pair_warnings}}`
- Cross-knowledge asymmetries (Spec 131): `{{knowledge_asymmetries}}`

## I. Anchor-checks
<!-- Source: Spec 140 — R-rules + motif/anchor pre-flight -->
- R-rules required: `{{required_rules}}`
- Recent anchor payoffs upstream: `{{recent_payoffs}}`
- Sensory-anchor lock (KW transition?): `{{kw_transition}}`

## J. Adversarial checks
<!-- Source: Spec 122 editorial gates (filter-words, show-don't-tell) +
     project R-rules (Spec 140) — run after draft, listed here for awareness -->
- Critical gates (block at): `{{critical_gates}}`
- Medium gates (review-warn): `{{medium_gates}}`
- Low gates (review-note): `{{low_gates}}`

## K. Cross-references
<!-- Source: Spec 132 codex matches + Spec 133 structure FULFILS + Spec 141 ModeBlock siblings -->
- Codex entries likely to inject: `{{codex_matches}}`
- Sibling chapters in same ModeBlock: `{{sibling_chapters}}`
- Mirror chapters (e.g. Ouroboros bracket 0/40, 1/39): `{{mirror_chapters}}`
- Promised callbacks upstream: `{{upstream_callbacks}}`

## L. Open questions
<!-- Source: Spec 137 canon-locks — gap [L] markers + unresolved proposals [V] -->
- Open [L] gaps touching this chapter: `{{open_gaps}}`
- [V] proposals to validate before drafting: `{{open_proposals}}`
- [S] quarry to consider mining: `{{quarry_candidates}}`

## M. Pre-draft checklist
<!-- Source: Spec 141 briefing_checklist verb — 7 items -->
- [ ] Storyform-status consistent (Spec 136)
- [ ] Voice-DNA anchor chosen (Spec 134/138)
- [ ] Hot-polarity checked (R-5; Spec 140)
- [ ] Genesis-echo limit (R-7; Spec 140)
- [ ] Reveal-layer checked (Spec 139)
- [ ] Ouroboros-duty satisfied (only for chapters 0 / 1 / 39 / 40 — KP-specific)
- [ ] R-rule pre-check complete (Spec 140 run_project_rules dry-run)

Drafted: `{{drafted_on}}`  ·  Briefer: `{{author_slug}}`  ·  Locks consulted: `{{locks_consulted}}`
