<!-- agency-generated: v1 -->
# novel.list_structure_templates

Discover the available story-structure templates (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `none.` |  |  |

## Returns

``{templates: [{template_id, name, source, beat_count}]}`` — the five vendored beat sheets ∪ any ``.agency/structure-templates-overlay.yaml`` additions.

## Chain-next

``novel.get_structure_template(template_id)`` for the full beat list; ``novel.apply_structure`` to commit one.

## Details

(no further detail)

## Example

```bash
agency-novel-list_structure_templates --intent-id $IID …
```
