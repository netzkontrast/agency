<!-- agency-generated: v1 -->
# novel.novel_progress

Aggregate progress (word-count + per-status counts) for a novel (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{novel_id, chapter_count, word_count_total, by_status}``.

## Chain-next

``novel.render_manuscript`` once status counts say ready.

## Details

(no further detail)

## Example

```bash
agency-novel-novel_progress --intent-id $IID …
```
