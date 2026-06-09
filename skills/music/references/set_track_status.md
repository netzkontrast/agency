<!-- agency-generated: v1 -->
# music.set_track_status

Persist a track's production status via the StateDriver (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album (slug), track (slug), status (one of ``TRACK_STATUS``).` |  |  |

## Returns

``{album, track, status}``.

## Chain-next

``music.list_tracks`` to verify, then ``music.album_progress``.

## Details

(no further detail)

## Example

```bash
agency-music-set_track_status --intent-id $IID …
```
