<!-- agency-generated: v1 -->
# prompt.catalog_list

List bundled CatalogModule entries optionally filtered by category (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `category (one of CATALOG_CATEGORY or ``""`` for all).` |  |  |

## Returns

``{modules: [{category, identifier, name, summary}], count}``.

## Chain-next

``prompt.brief_render`` with the selected module identifiers.

## Details

Slice 1 ships a 6-module seed (M01-M06 across categories A/B/C); Slice 2 loads the full catalog from ``data/reference/research-module-catalog.yaml``.

## Example

```bash
agency-prompt-catalog_list --intent-id $IID …
```
