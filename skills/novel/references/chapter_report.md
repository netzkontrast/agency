<!-- agency-generated: v1 -->
# novel.chapter_report

Read-only aggregate over the novel's chapters (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{novel_id, chapter_count, word_count_total, by_status}``.

## Chain-next

revise chapters then ``novel.render_manuscript``.

## Details

(no further detail)

## Example

```bash
agency-novel-chapter_report --intent-id $IID …
```
