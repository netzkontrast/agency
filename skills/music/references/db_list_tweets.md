<!-- agency-generated: v1 -->
# music.db_list_tweets

List tweets via the DBDriver, filtered by album + status (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, status, limit.` |  |  |

## Returns

``{tweets, count, album, status}``.

## Chain-next

``music.tweet_schedule_gate`` per row.

## Details

(no further detail)

## Example

```bash
agency-music-db_list_tweets --intent-id $IID …
```
