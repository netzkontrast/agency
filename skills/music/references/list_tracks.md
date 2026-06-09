<!-- agency-generated: v1 -->
# music.list_tracks

List tracks for an album via the StateDriver (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album (slug).` |  |  |

## Returns

``{album, tracks: [{slug, title, status, …}], count}``.

## Chain-next

``music.album_progress`` for the aggregate view.

## Details

(no further detail)

## Example

```bash
agency-music-list_tracks --intent-id $IID …
```
