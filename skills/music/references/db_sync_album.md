<!-- agency-generated: v1 -->
# music.db_sync_album

Idempotent sync of an album's tweets — replaces existing (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, tweets (list of {body, scheduled_at, platform}).` |  |  |

## Returns

``{album, removed, created}``.

## Chain-next

``music.db_list_tweets(album)`` to verify.

## Details

(no further detail)

## Example

```bash
agency-music-db_sync_album --intent-id $IID …
```
