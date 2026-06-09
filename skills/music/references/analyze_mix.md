<!-- agency-generated: v1 -->
# music.analyze_mix

Analyse a mix for loudness issues via the AudioDriver (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, path.` |  |  |

## Returns

``{album, measured_lufs, findings}`` — decidable findings (too hot > -9, too quiet < -16).

## Chain-next

``music.master_album``.

## Details

(no further detail)

## Example

```bash
agency-music-analyze_mix --intent-id $IID …
```
