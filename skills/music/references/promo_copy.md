<!-- agency-generated: v1 -->
# music.promo_copy

Draft promotional copy for an album (act, produces a ``promo-copy`` artefact).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, angle.` |  |  |

## Returns

``{result, artefact}`` where artefact.kind = ``promo-copy``.

## Chain-next

``music.publish_asset`` the copy.

## Details

(no further detail)

## Example

```bash
agency-music-promo_copy --intent-id $IID …
```
