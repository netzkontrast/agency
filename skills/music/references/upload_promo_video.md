<!-- agency-generated: v1 -->
# music.upload_promo_video

Upload a promo video to object storage (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, key (R2 object key), body (video bytes).` |  |  |

## Returns

``{result, artefact}`` published-asset artefact.

## Chain-next

``music.r2_signed_url`` to share.

## Details

Promo-video-specific wrapper that records a ``published-asset`` artefact tagged ``promo-video``.

## Example

```bash
agency-music-upload_promo_video --intent-id $IID …
```
