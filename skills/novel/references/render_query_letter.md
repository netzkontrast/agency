<!-- agency-generated: v1 -->
# novel.render_query_letter

Render an agent query letter (act, driver-free).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, agent_name, comp_titles (comparable titles).` |  |  |

## Returns

``{result, artefact}`` query-letter artefact.

## Chain-next

``novel.render_synopsis`` to bundle the submission.

## Details

(no further detail)

## Example

```bash
agency-novel-render_query_letter --intent-id $IID …
```
