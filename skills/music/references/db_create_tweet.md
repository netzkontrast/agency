<!-- agency-generated: v1 -->
# music.db_create_tweet

Insert a tweet row via the DBDriver, producing a tweet-record artefact (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, body, scheduled_at (ISO), platform (default ``x``).` |  |  |

## Returns

``{result, artefact}`` tweet-record artefact with tweet_id.

## Chain-next

``music.db_update_tweet`` to flip status; ``music.tweet_schedule_gate``.

## Details

(no further detail)

## Example

```bash
agency-music-db_create_tweet --intent-id $IID …
```
