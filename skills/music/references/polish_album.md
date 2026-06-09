<!-- agency-generated: v1 -->
# music.polish_album

Album-wide polish pass — applies polish to every track (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, paths (list of track WAV paths).` |  |  |

## Returns

``{album, polished: [...], count}``.

## Chain-next

``music.polish_and_master_album`` or per-track master.

## Details

(no further detail)

## Example

```bash
agency-music-polish_album --intent-id $IID …
```
