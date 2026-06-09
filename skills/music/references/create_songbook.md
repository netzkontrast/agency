<!-- agency-generated: v1 -->
# music.create_songbook

LilyPond → PDF songbook render via AudioDriver (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, tracks (list of track titles or musicxml paths).` |  |  |

## Returns

``{result, artefact}`` sheet-music artefact (PDF stub).

## Chain-next

``music.publish_asset`` the songbook.

## Details

(no further detail)

## Example

```bash
agency-music-create_songbook --intent-id $IID …
```
