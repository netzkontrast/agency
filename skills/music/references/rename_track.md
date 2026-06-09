<!-- agency-generated: v1 -->
# music.rename_track

Rename a track within an album, mirroring paths via the StateDriver (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, old_slug, new_slug.` |  |  |

## Returns

``{success, album_slug, old_slug, new_slug, title}``.

## Chain-next

``music.list_tracks`` to verify.

## Details

(no further detail)

## Example

```bash
agency-music-rename_track --intent-id $IID …
```
