<!-- agency-generated: v1 -->
# music.fix_dynamic_track

Dynamic range fixer — applies compression/expansion (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, path, target_dr (default 8.0).` |  |  |

## Returns

``{album, path, measured_dr, target_dr, applied, output}``.

## Chain-next

``music.qc_audio`` to verify.

## Details

(no further detail)

## Example

```bash
agency-music-fix_dynamic_track --intent-id $IID …
```
