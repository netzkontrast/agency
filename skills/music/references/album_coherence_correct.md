<!-- agency-generated: v1 -->
# music.album_coherence_correct

Apply coherence corrections to bring outliers in line (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, paths, target (e.g. ``{centroid_hz` |  | 2500}``). |

## Returns

``{album, applied_to, target, ok}``.

## Chain-next

``music.album_coherence_check`` to verify.

## Details

(no further detail)

## Example

```bash
agency-music-album_coherence_correct --intent-id $IID …
```
