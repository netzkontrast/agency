<!-- agency-generated: v1 -->
# novel.set_chapter_status

Flip a Chapter's lifecycle status; enum-checked (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `chapter_id, status (one of ``CHAPTER_STATUS``).` |  |  |

## Returns

``{chapter_id, status}``.

## Chain-next

``novel.novel_progress`` to see the aggregate shift.

## Details

(no further detail)

## Example

```bash
agency-novel-set_chapter_status --intent-id $IID …
```
