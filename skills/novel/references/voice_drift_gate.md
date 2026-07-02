<!-- agency-generated: v1 -->
# novel.voice_drift_gate

Composite gate: passes IFF every POV scene with a profiled character scores ≥ ``min_score`` (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, min_score (default 70).` |  |  |

## Returns

``{passed, checked, failing: [{scene_id, character_id, score}]}``.

## Chain-next

revise failing scenes, re-run; ``novel.line_gate``.

## Details

(no further detail)

## Example

```bash
agency-novel-voice_drift_gate --intent-id $IID …
```
