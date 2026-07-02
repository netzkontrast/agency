<!-- agency-generated: v1 -->
# novel.get_structure_template

Read one template's full body — every beat with its position + author-facing prompt (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `template_id.` |  |  |

## Returns

``{template_id, name, source, beats: [{slug, name, position, prompt}]}``; NOT_FOUND for an unknown id.

## Chain-next

``novel.apply_structure(novel_id, template_id)``.

## Details

(no further detail)

## Example

```bash
agency-novel-get_structure_template --intent-id $IID …
```
