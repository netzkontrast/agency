<!-- agency-generated: v1 -->
# adr.supersede

SUPERSEDE — the SPEC-001-C automatic actions: mint a replacement ``Decision`` (status ``proposed``) ``PART_OF`` the same theme, flip the old one to ``superseded``, and write the forward reference (the core ``SUPERSEDED_BY`` edge).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `old_id (the decision being replaced), plus the new WH(Y) fields (same shape as `draft`).` |  |  |

## Returns

``{old_id, new_id, status: "superseded", theme_id}`` or ``{error}``.

## Chain-next

adr.validate(new_id); adr.render(theme_id).

## Details

(no further detail)

## Example

```bash
agency-adr-supersede --intent-id $IID …
```
