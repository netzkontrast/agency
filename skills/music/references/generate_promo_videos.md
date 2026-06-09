<!-- agency-generated: v1 -->
# music.generate_promo_videos

Render a vertical promo video via AudioDriver (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, audio (track path), art (cover-art path), template.` |  |  |

## Returns

``{result, artefact}`` promo-video artefact.

## Chain-next

``music.publish_asset`` the video.

## Details

(no further detail)

## Example

```bash
agency-music-generate_promo_videos --intent-id $IID …
```
