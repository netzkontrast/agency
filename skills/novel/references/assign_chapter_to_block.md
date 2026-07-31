<!-- agency-generated: v1 -->
# novel.assign_chapter_to_block

Bind a chapter to its block via ``IN_MODE_BLOCK`` (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `chapter_id, mode_block_id.` |  |  |

## Returns

``{chapter_id, mode_block_id}``.

## Chain-next

``novel.mode_block_report(novel_id)``.

## Details

(no further detail)

## Example

```bash
agency-novel-assign_chapter_to_block --intent-id $IID …
```
