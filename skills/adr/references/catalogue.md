<!-- agency-generated: v1 -->
# adr.catalogue

CATALOGUE — the "handful of ADRs" index (SPEC-001-B minimalism): every theme + its `PART_OF` decision counts grouped by status.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `status (str — count only this decision status), layer (str — only this theme's layer).` |  |  |

## Returns

``{themes: [{id, layer, title, decisions, by_status}], total_themes, total_decisions}``.

## Chain-next

adr.theme_status(theme_id) for one theme's aggregate; adr.render(theme_id) to project its live decisions.

## Details

(Named `catalogue`, not `list`, to avoid a bare-name collision with `manage.list` — Spec 074 collision discipline.)

## Example

```bash
agency-adr-catalogue --intent-id $IID …
```
