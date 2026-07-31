<!-- agency-generated: v1 -->
# novel.render_chapter_briefing

Compose the 13-section chapter briefing (act) — AGGREGATES the whole KP stack (mode-block 141, storyform routing 136, alters/voice 138, reveals 139, motifs/anchors/R-rules 140) into the vendored template; records a ``chapter-briefing`` Artefact.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `chapter_id.` |  |  |

## Returns

``{content, artefact_id, chapter_id}``.

## Chain-next

fill the — slots by hand; ``novel.briefing_checklist``.

## Details

(no further detail)

## Example

```bash
agency-novel-render_chapter_briefing --intent-id $IID …
```
