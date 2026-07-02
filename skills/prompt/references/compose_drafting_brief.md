<!-- agency-generated: v1 -->
# prompt.compose_drafting_brief

Compose the LLM-side drafting brief for ONE scene (transform; Spec 143) — the prompt counterpart of Spec 127's graph-side ``assemble_scene_brief``.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id, max_tokens.` |  |  |

## Returns

``{brief, sources: [slug], total_tokens}``.

## Chain-next

feed ``brief`` as the system prompt of the scene draft.

## Details

(no further detail)

## Example

```bash
agency-prompt-compose_drafting_brief --intent-id $IID …
```
