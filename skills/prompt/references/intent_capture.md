<!-- agency-generated: v1 -->
# prompt.intent_capture

Record a structured ResearchIntent SERVING the intent (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `seed_query, topic, deliverable (one of DELIVERABLE_KIND), success_criteria (multi-line).` |  |  |

## Returns

``{intent_id, deliverable}``.

## Chain-next

``prompt.catalog_list`` then ``prompt.brief_render``.

## Details

(no further detail)

## Example

```bash
agency-prompt-intent_capture --intent-id $IID …
```
