<!-- agency-generated: v1 -->
# novel.render_chapter_brief

Produce a research-dossier brief tied to a chapter (act, xcap to prompt).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `chapter_id, research_intent_id (optional).` |  |  |

## Returns

``{result, artefact}`` research-dossier.

## Chain-next

``novel.dispatch_novel_research`` if more sources needed.

## Details

Gathers chapter context (parent novel title, chapter title + body preview) and renders a research-dossier artefact. When ``research_intent_id`` is supplied, chains ``prompt.brief_render`` to weave the dossier into the body; otherwise renders a minimal body from chapter context alone.

## Example

```bash
agency-novel-render_chapter_brief --intent-id $IID …
```
