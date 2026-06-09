<!-- agency-generated: v1 -->
# novel.create_novel

Record a Novel node SERVING the intent (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `title, author.` |  |  |

## Returns

``{novel_id, title, status}``.

## Chain-next

``novel.create_chapter`` once outline is ready.

## Details

(no further detail)

## Example

```bash
agency-novel-create_novel --intent-id $IID …
```
