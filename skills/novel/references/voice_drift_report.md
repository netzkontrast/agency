<!-- agency-generated: v1 -->
# novel.voice_drift_report

Full-manuscript voice audit (transform): every POV scene scored against its character's profile, worst-first per character; the bottom 10% manuscript-wide flagged as outliers.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{by_character: {character_id: [{scene_id, score}]}, manuscript_outliers: [{scene_id, score}]}``.

## Chain-next

revise the outlier scenes; ``novel.voice_drift_gate``.

## Details

(no further detail)

## Example

```bash
agency-novel-voice_drift_report --intent-id $IID …
```
