<!-- agency-generated: v1 -->
# music.publish_sheet_music

Publish a sheet-music PDF to object storage (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, key (the R2 object key), body (PDF bytes).` |  |  |

## Returns

``{result, artefact}`` published-asset artefact.

## Chain-next

``music.r2_signed_url`` to share.

## Details

Sheet-music-specific wrapper around ``publish_asset`` that records a ``published-asset`` artefact tagged ``sheet-music``.

## Example

```bash
agency-music-publish_sheet_music --intent-id $IID …
```
