<!-- agency-generated: v1 -->
# music.db_search_tweets

Substring search across tweet bodies via DBDriver (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `query, limit.` |  |  |

## Returns

``{tweets, count, query}``.

## Chain-next

``music.db_update_tweet`` to revise hits.

## Details

(no further detail)

## Example

```bash
agency-music-db_search_tweets --intent-id $IID …
```
