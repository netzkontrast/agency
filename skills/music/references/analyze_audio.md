<!-- agency-generated: v1 -->
# music.analyze_audio

General spectral + loudness probe via AudioDriver (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, path.` |  |  |

## Returns

``{album, loudness_lufs, signature: {…}}``.

## Chain-next

``music.qc_audio`` for the full QC pass.

## Details

(no further detail)

## Example

```bash
agency-music-analyze_audio --intent-id $IID …
```
