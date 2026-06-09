<!-- agency-generated: v1 -->
# music.db_delete_tweet

Delete a tweet row via the DBDriver (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `tweet_id.` |  |  |

## Returns

``{tweet_id, deleted}``.

## Chain-next

``music.db_list_tweets`` to verify.

## Details

(no further detail)

## Example

```bash
agency-music-db_delete_tweet --intent-id $IID …
```
