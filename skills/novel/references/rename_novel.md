<!-- agency-generated: v1 -->
# novel.rename_novel

Update a Novel's title (effect, graph-only).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, new_title.` |  |  |

## Returns

``{novel_id, title}``.

## Chain-next

continue authoring; the rename is auditable via the graph's bi-temporal stamp.

## Details

(no further detail)

## Example

```bash
agency-novel-rename_novel --intent-id $IID …
```
