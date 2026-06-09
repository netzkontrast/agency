<!-- agency-generated: v1 -->
# music.get_promo_status

Per-album promo state via StateDriver + DBDriver (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album.` |  |  |

## Returns

``{album, tweets: {total, by_status}, streaming_urls: int}``.

## Chain-next

``music.tweet-curation`` skill walk for any pending tweets.

## Details

(no further detail)

## Example

```bash
agency-music-get_promo_status --intent-id $IID …
```
