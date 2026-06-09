<!-- agency-generated: v1 -->
# music.album_coherence_check

Cross-track tonal coherence report via AudioDriver (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, paths.` |  |  |

## Returns

``{album, coherent, avg_distance, outliers, track_count}``.

## Chain-next

``music.album_coherence_correct`` if outliers found.

## Details

(no further detail)

## Example

```bash
agency-music-album_coherence_check --intent-id $IID …
```
