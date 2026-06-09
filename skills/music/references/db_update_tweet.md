<!-- agency-generated: v1 -->
# music.db_update_tweet

Update tweet row fields via the DBDriver (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `tweet_id, fields (dict of {field` |  | value}). |

## Returns

``{tweet_id, fields}``.

## Chain-next

``music.db_list_tweets`` to verify.

## Details

(no further detail)

## Example

```bash
agency-music-db_update_tweet --intent-id $IID …
```
