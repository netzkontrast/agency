<!-- agency-generated: v1 -->
# novel.score_voice_match

Score prose against the character's profile — 0–100, equal-weighted across the SET fields (transform; OQ2 v1).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `character_id, body (the prose to score).` |  |  |

## Returns

``{score, deviations: [{field, target, actual, severity}]}``.

## Chain-next

revise the prose, or ``novel.update_voice_profile`` if the profile itself is wrong.

## Details

(no further detail)

## Example

```bash
agency-novel-score_voice_match --intent-id $IID …
```
