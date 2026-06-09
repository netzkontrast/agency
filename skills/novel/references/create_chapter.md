<!-- agency-generated: v1 -->
# novel.create_chapter

Record a Chapter graph node + CHAPTER_OF the parent Novel (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, number (1-indexed), title, body (optional draft body).` |  |  |

## Returns

``{chapter_id, novel_id, number, title, status}``.

## Chain-next

``novel.chapter_report`` to aggregate state.

## Details

(no further detail)

## Example

```bash
agency-novel-create_chapter --intent-id $IID …
```
