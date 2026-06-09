<!-- agency-generated: v1 -->
---
name: novel
description: Use when authoring a novel — turning a premise into a structured manuscript through gated concept → chapters → report → render.
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---

# novel capability

Five-verb path from premise to manuscript: conceptualize → create_novel → create_chapter → chapter_report → render_manuscript, plus the novel-concept gated planning skill.

## When to use

- A novel premise needs structured planning before drafting
- A chapter needs a per-chapter report (word count, beat progress)
- A finished draft needs rendering to manuscript format

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `analyze_readability` | transform | Flesch Reading Ease for prose (transform, driver-free). | [details](#analyze_readability) |
| `capture_claim` | effect | Record a NovelClaim node SERVING the intent (effect). | [details](references/capture_claim.md) |
| `capture_idea` | effect | Record an Idea node SERVING the intent (effect). | [details](references/capture_idea.md) |
| `chapter_report` | transform | Read-only aggregate over the novel's chapters (transform). | [details](references/chapter_report.md) |
| `check_filter_words` | transform | Filter-word density check (transform, show-don't-tell). | [details](references/check_filter_words.md) |
| `check_throughline_partition` | transform | Decidable check (row 5): 4 throughlines / 4 distinct Classes (transform). | [details](references/check_throughline_partition.md) |
| `conceptualize` | act | Render a novel-concept document (act); the first verb of the MVN flow. | [details](references/conceptualize.md) |
| `count_words` | transform | Word + char counter (transform, driver-free). | [details](#count_words) |
| `create_chapter` | effect | Record a Chapter graph node + CHAPTER_OF the parent Novel (effect). | [details](references/create_chapter.md) |
| `create_novel` | effect | Record a Novel node SERVING the intent (effect). | [details](references/create_novel.md) |
| `create_scene` | effect | Record a Scene node + SCENE_OF the parent Chapter (effect). | [details](references/create_scene.md) |
| `find_novel` | transform | Substring-match novel titles (transform, driver-free). | [details](references/find_novel.md) |
| `list_chapters` | transform | List a novel's chapters ordered by number (transform). | [details](references/list_chapters.md) |
| `list_claims` | transform | List captured claims; optional verified-status filter (transform). | [details](references/list_claims.md) |
| `list_ideas` | transform | List captured ideas; optional status filter (transform). | [details](references/list_ideas.md) |
| `manuscript_coherence_check` | transform | Chapter-sequence contiguity check (transform, driver-free). | [details](references/manuscript_coherence_check.md) |
| `novel_progress` | transform | Aggregate progress (word-count + per-status counts) for a novel (transform). | [details](references/novel_progress.md) |
| `pending_verifications` | transform | Aggregate pending claims by domain (transform). | [details](references/pending_verifications.md) |
| `pre_draft_gate` | effect | Composite gate: storyform + research + chapters present (effect). | [details](references/pre_draft_gate.md) |
| `promote_idea` | effect | Idea → Novel transition; records PROMOTED_TO edge (effect). | [details](references/promote_idea.md) |
| `rename_novel` | effect | Update a Novel's title (effect, graph-only). | [details](references/rename_novel.md) |
| `render_blurb` | act | Render a back-cover blurb (act, driver-free). | [details](references/render_blurb.md) |
| `render_manuscript` | act | Concatenate chapters into a manuscript artefact (act). | [details](references/render_manuscript.md) |
| `render_query_letter` | act | Render an agent query letter (act, driver-free). | [details](references/render_query_letter.md) |
| `render_synopsis` | act | Render a synopsis from chapter outline (act, driver-free). | [details](references/render_synopsis.md) |
| `resume_session` | transform | Return the most-recently-created Novel's id + title (transform). | [details](references/resume_session.md) |
| `set_chapter_status` | effect | Flip a Chapter's lifecycle status; enum-checked (effect). | [details](references/set_chapter_status.md) |
| `set_novel_status` | effect | Flip a Novel's lifecycle status; enum-checked (effect). | [details](references/set_novel_status.md) |

## Example

```bash
await call_tool('capability_novel_analyze_readability', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Hand-rolling chapter files outside the capability → call `novel.create_chapter`
- Skipping the conceptualizer's hard gate → walk `novel-concept`

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`novel-concept`** (conceptualizer): premise → genre → audience → pov → setting → characters-core → dramatica-seed → outline-shape → series-hypothesis → confirmation
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'novel-concept', 'inputs': {}, 'intent_id': '…'})`

## analyze_readability

Flesch Reading Ease for prose (transform, driver-free).

Parameters: `(body: 'str')`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/analyze_readability.md.)_

## count_words

Word + char counter (transform, driver-free).

Parameters: `(body: 'str')`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/count_words.md.)_
