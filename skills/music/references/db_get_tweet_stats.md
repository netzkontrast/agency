<!-- agency-generated: v1 -->
# music.db_get_tweet_stats

Aggregate counts of tweets by status via DBDriver (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album (empty = all albums).` |  |  |

## Returns

``{album, total, by_status}``.

## Chain-next

``music.tweet-curation`` skill walk.

## Details

(no further detail)

## Example

```bash
agency-music-db_get_tweet_stats --intent-id $IID …
```
