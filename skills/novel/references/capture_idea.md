<!-- agency-generated: v1 -->
# novel.capture_idea

Record an Idea node SERVING the intent (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `text.` |  |  |

## Returns

``{idea_id, text, status}``.

## Chain-next

``novel.promote_idea`` once the premise hardens.

## Details

Pre-novel capture surface: free-text premise jotted before the gated conceptualizer runs. Default status ``new``.

## Example

```bash
agency-novel-capture_idea --intent-id $IID …
```
