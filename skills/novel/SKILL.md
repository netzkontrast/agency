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
| `capture_idea` | effect | Record an Idea node SERVING the intent (effect). | [details](references/capture_idea.md) |
| `chapter_report` | transform | Read-only aggregate over the novel's chapters (transform). | [details](references/chapter_report.md) |
| `check_throughline_partition` | transform | Decidable check (row 5): 4 throughlines / 4 distinct Classes (transform). | [details](references/check_throughline_partition.md) |
| `conceptualize` | act | Render a novel-concept document (act); the first verb of the MVN flow. | [details](references/conceptualize.md) |
| `create_chapter` | effect | Record a Chapter graph node + CHAPTER_OF the parent Novel (effect). | [details](references/create_chapter.md) |
| `create_novel` | effect | Record a Novel node SERVING the intent (effect). | [details](references/create_novel.md) |
| `find_novel` | transform | Substring-match novel titles (transform, driver-free). | [details](references/find_novel.md) |
| `list_ideas` | transform | List captured ideas; optional status filter (transform). | [details](references/list_ideas.md) |
| `promote_idea` | effect | Idea → Novel transition; records PROMOTED_TO edge (effect). | [details](references/promote_idea.md) |
| `render_manuscript` | act | Concatenate chapters into a manuscript artefact (act). | [details](references/render_manuscript.md) |
| `set_novel_status` | effect | Flip a Novel's lifecycle status; enum-checked (effect). | [details](references/set_novel_status.md) |

## Example

```bash
await call_tool('capability_novel_capture_idea', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Hand-rolling chapter files outside the capability → call `novel.create_chapter`
- Skipping the conceptualizer's hard gate → walk `novel-concept`

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`novel-concept`** (conceptualizer): premise → genre → audience → pov → setting → characters-core → dramatica-seed → outline-shape → series-hypothesis → confirmation
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'novel-concept', 'inputs': {}, 'intent_id': '…'})`
