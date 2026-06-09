<!-- agency-generated: v1 -->
# music.conceptualize

Render an album-concept document (act); ``type`` must be a known album type.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `artist, title, type (one of ``ALBUM_TYPES``), theme, tracklist.` |  |  |

## Returns

``{result, artefact}`` where artefact.kind = ``album-concept``.

## Chain-next

``music.lyric_report`` for prosody analysis, then ``music.master_album``.

## Details

(no further detail)

## Example

```bash
agency-music-conceptualize --intent-id $IID …
```
