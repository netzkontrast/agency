<!-- agency-generated: v1 -->
# music.create_track

Create a track in an album, rendered from the bitwize ``track`` template (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album (slug), title, track_number (0-padded to 2 digits in the slug).` |  |  |

## Returns

``{track_id, track_slug, album, track_number, title}``.

## Chain-next

``music.set_track_status`` as the track progresses.

## Details

Records a ``Track`` graph node, edges ``Track RECORDED_FOR Album``, persists via the StateDriver.

## Example

```bash
agency-music-create_track --intent-id $IID …
```
