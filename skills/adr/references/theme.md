<!-- agency-generated: v1 -->
# adr.theme

THEME — get-or-create a thematic-living ADR for one architecture ``layer`` (the ported Master ADR).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `layer (str — e.g. "datalayer"), title (str), scope (str — the Master-ADR scope boundary).` |  |  |

## Returns

``{id, layer, created}``.

## Chain-next

adr.draft(theme_id, decision=…) to record a decision under it.

## Details

(no further detail)

## Example

```bash
agency-adr-theme --intent-id $IID …
```
