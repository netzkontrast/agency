<!-- agency-generated: v1 -->
# novel.render_blurb

Render a back-cover blurb (act, driver-free).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, hook (one-sentence premise), stakes.` |  |  |

## Returns

``{result, artefact}`` blurb artefact.

## Chain-next

``novel.render_query_letter`` for the agent submission.

## Details

(no further detail)

## Example

```bash
agency-novel-render_blurb --intent-id $IID …
```
