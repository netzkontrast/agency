<!-- agency-generated: v1 -->
# novel.render_synopsis

Render a synopsis from chapter outline (act, driver-free).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{result, artefact}`` synopsis artefact with chapters in order.

## Chain-next

``novel.render_query_letter`` for the submission.

## Details

(no further detail)

## Example

```bash
agency-novel-render_synopsis --intent-id $IID …
```
