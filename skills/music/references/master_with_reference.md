<!-- agency-generated: v1 -->
# music.master_with_reference

Master `path` to match `reference` album loudness (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, path, reference (the reference WAV path).` |  |  |

## Returns

``{result, artefact}`` mastering-report.

## Chain-next

``music.album_coherence_check`` to verify match.

## Details

(no further detail)

## Example

```bash
agency-music-master_with_reference --intent-id $IID …
```
