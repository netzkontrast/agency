<!-- agency-generated: v1 -->
# novel.check_pov_voice

Gate a scene's body against its POV character's profile (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id.` |  |  |

## Returns

``{passed, score, deviations, character_id}`` — pass threshold 70 (``VOICE_PASS_THRESHOLD``).

## Chain-next

revise the scene, or ``novel.voice_drift_report`` for the manuscript view.

## Details

(no further detail)

## Example

```bash
agency-novel-check_pov_voice --intent-id $IID …
```
