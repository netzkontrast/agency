<!-- agency-generated: v1 -->
# music.set_album_status

Persist an album's production status via the StateDriver (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, status (one of the Album.status enum).` |  |  |

## Returns

``{album, status}`` echoing the persisted record.

## Chain-next

``release-qa``.

## Details

(no further detail)

## Example

```bash
agency-music-set_album_status --intent-id $IID …
```
