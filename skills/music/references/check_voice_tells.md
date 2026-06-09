<!-- agency-generated: v1 -->
# music.check_voice_tells

AI-tell rule-based detector (advisory only — no gate impact) (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lyrics.` |  |  |

## Returns

``{findings: [{heuristic, severity, fix}], count}``.

## Chain-next

rewrite flagged lines for idiosyncrasy.

## Details

(no further detail)

## Example

```bash
agency-music-check_voice_tells --intent-id $IID …
```
