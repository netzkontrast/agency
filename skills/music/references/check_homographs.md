<!-- agency-generated: v1 -->
# music.check_homographs

Flag words with multiple legitimate pronunciations (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lyrics.` |  |  |

## Returns

``{findings: [{word, ambiguous_readings, severity}], count}``.

## Chain-next

``music.pronunciation_gate``.

## Details

(no further detail)

## Example

```bash
agency-music-check_homographs --intent-id $IID …
```
