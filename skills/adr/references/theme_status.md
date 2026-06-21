<!-- agency-generated: v1 -->
# adr.theme_status

THEME_STATUS — the SPEC-001-D aggregate status DERIVED from the theme's ``PART_OF`` children (never stored — rule 8).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `theme_id (str).` |  |  |

## Returns

``{theme_id, status, counts: {status: n}, children}``.

## Chain-next

adr.render(theme_id) to project the live decisions.

## Details

(no further detail)

## Example

```bash
agency-adr-theme_status --intent-id $IID …
```
