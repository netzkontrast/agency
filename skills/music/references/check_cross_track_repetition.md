<!-- agency-generated: v1 -->
# music.check_cross_track_repetition

Flag lyric lines repeated across multiple album tracks (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `tracks (list of lyric bodies, one per track).` |  |  |

## Returns

``{repeated_lines, track_count, examples}``.

## Chain-next

``music.repetition_gate``.

## Details

(no further detail)

## Example

```bash
agency-music-check_cross_track_repetition --intent-id $IID …
```
