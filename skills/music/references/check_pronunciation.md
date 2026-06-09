<!-- agency-generated: v1 -->
# music.check_pronunciation

Flag words requiring forced pronunciation per the bundled guide (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lyrics (multi-line text).` |  |  |

## Returns

``{findings: [{word, suggested, severity}], count}``.

## Chain-next

``music.pronunciation_gate`` to gate the lyric-writing skill.

## Details

(no further detail)

## Example

```bash
agency-music-check_pronunciation --intent-id $IID …
```
