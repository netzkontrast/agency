<!-- agency-generated: v1 -->
# music.get_promo_content

Read promo content (drafts + scheduled tweets) via DBDriver (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album.` |  |  |

## Returns

``{album, drafts, scheduled, total}``.

## Chain-next

``music.db_update_tweet`` to advance status.

## Details

(no further detail)

## Example

```bash
agency-music-get_promo_content --intent-id $IID …
```
