<!-- agency-generated: v1 -->
# music.get_streaming_urls

Read recorded streaming URLs for an album via StateDriver (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album.` |  |  |

## Returns

``{album, urls: [{platform, url}]}``.

## Chain-next

``music.verify_streaming`` to re-check.

## Details

(no further detail)

## Example

```bash
agency-music-get_streaming_urls --intent-id $IID …
```
