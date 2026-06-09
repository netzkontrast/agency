<!-- agency-generated: v1 -->
# music.render_codec_preview

Render a streaming-codec preview via AudioDriver (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, path, codec (one of aac/opus/mp3).` |  |  |

## Returns

``{album, path, codec, output, bitrate_kbps}``.

## Chain-next

``music.publish_asset`` the preview.

## Details

(no further detail)

## Example

```bash
agency-music-render_codec_preview --intent-id $IID …
```
