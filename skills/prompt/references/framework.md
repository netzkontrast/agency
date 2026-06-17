<!-- agency-generated: v1 -->
# prompt.framework

Look up a single prompt-engineering framework by slug (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `slug (str — e.g. ``co-star``, ``ape``, ``rise-ie``).` |  |  |

## Returns

``{slug, name, intent_category, complexity_tier, components, template, when_to_use, tokens}`` OR ``{slug, error: 'NO_FRAMEWORK'}`` when no framework carries that slug.

## Chain-next

``prompt.render(slug, fields)`` to fill its template.

## Details

(no further detail)

## Example

```bash
agency-prompt-framework --intent-id $IID …
```
