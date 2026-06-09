<!-- agency-generated: v1 -->
# novel.resume_session

Return the most-recently-created Novel's id + title (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `none.` |  |  |

## Returns

``{novel_id, title}`` — empty strings when no Novel exists.

## Chain-next

typically ``novel.novel_progress(novel_id)`` to land in the right state on session resume.

## Details

(no further detail)

## Example

```bash
agency-novel-resume_session --intent-id $IID …
```
