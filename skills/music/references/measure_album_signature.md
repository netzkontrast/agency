<!-- agency-generated: v1 -->
# music.measure_album_signature

Spectral signatures for an album's tracks via AudioDriver (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, paths.` |  |  |

## Returns

``{album, signatures: [{path, centroid_hz, …}], count}``.

## Chain-next

``music.album_coherence_check``.

## Details

(no further detail)

## Example

```bash
agency-music-measure_album_signature --intent-id $IID …
```
