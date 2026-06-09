<!-- agency-generated: v1 -->
# music.catalogue_gate

Catalogue-synced gate — streaming URLs + tweets ready (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, album.` |  |  |

## Returns

``{gate, passed, streaming_urls, scheduled_tweets}``.

## Chain-next

``music.update_streaming_url`` and ``music.db_create_tweet``.

## Details

Passes iff at least 1 streaming URL is recorded AND at least 1 scheduled tweet exists for the album.

## Example

```bash
agency-music-catalogue_gate --intent-id $IID …
```
