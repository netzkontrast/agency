<!-- agency-generated: v1 -->
# music.rename_album

Rename an album, mirroring paths via the StateDriver (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `old_slug, new_slug.` |  |  |

## Returns

``{success, old_slug, new_slug, title, tracks_updated}``.

## Chain-next

``music.album_progress`` to verify state preserved.

## Details

(no further detail)

## Example

```bash
agency-music-rename_album --intent-id $IID …
```
