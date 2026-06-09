<!-- agency-generated: v1 -->
# prompt.brief_render

Render a ResearchBrief body from the dossier-skeleton template (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `research_intent_id (the ResearchIntent node id from ``prompt.intent_capture``; the reserved ``intent_id`` is the serving Intent so this verb's input is namespaced), module_ids (comma-separated CatalogModule identifiers, e.g. ``"M01,M03,M06"``).` |  |  |

## Returns

``{result, artefact}`` research-dossier artefact.

## Chain-next

``prompt.brief_audit`` to gate.

## Details

Records a ResearchBrief node + body; edges to the source ResearchIntent via RENDERS_FROM.

## Example

```bash
agency-prompt-brief_render --intent-id $IID …
```
