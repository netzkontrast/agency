<!-- agency-generated: v1 -->
# dogfood.render

Project plan_slug observations into DOGFOOD-NOTES.md.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `plan_slug (str — same shape as note's tag), max_tokens (int — wire-payload cap; default 5000 cl100k; additional observations get omitted with a "_… (N more omitted)_" marker).` |  |  |

## Returns

``{content, count, omitted, plan_slug, tokens}``. Empty plan returns clean markdown with "(none yet)" — never raises. Only Reflections with BOTH ``plan_slug == <slug>`` AND ``scope == 'observation'`` are surfaced (matches dogfood.note's write shape). Other-scope reflections + reflections without plan_slug are deliberately excluded.

## Chain-next

caller writes ``Plan/<slug>/DOGFOOD-NOTES.md`` IF a file projection is wanted (graph stays canonical).

## Details

(no further detail)

## Example

```bash
agency-dogfood-render --intent-id $IID …
```
