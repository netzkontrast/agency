<!-- agency-generated: v1 -->
# music.check_streaming_lyrics

Check the lyric body for platform-incompatible markup (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lyrics, platform (default ``spotify``).` |  |  |

## Returns

``{platform, bracket_tags, safe, fix?}``.

## Chain-next

strip bracket tags before upload if ``safe=False``.

## Details

(no further detail)

## Example

```bash
agency-music-check_streaming_lyrics --intent-id $IID …
```
