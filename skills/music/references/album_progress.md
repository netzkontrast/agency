<!-- agency-generated: v1 -->
# music.album_progress

Album progress aggregate via the StateDriver (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album (slug).` |  |  |

## Returns

``{album_slug, track_count, tracks_completed, completion_percentage, tracks_by_status}``.

## Chain-next

``music.release_check`` once completion_percentage = 100.

## Details

(no further detail)

## Example

```bash
agency-music-album_progress --intent-id $IID …
```
