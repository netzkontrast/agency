<!-- agency-generated: v1 -->
# novel.switching_log

Infer per scene which alter fronts (transform) — matched from the bound voice signatures against the scene body — plus the R-4 micro-cue count (max 3 per bridge).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `system_id, novel_id.` |  |  |

## Returns

``{scenes: [{scene_id, chapter, inferred_alter, confidence, micro_cue_count, exceeds_cue_cap}], summary}``.

## Chain-next

revise over-cued scenes; ``novel.check_alter_recognition``.

## Details

(no further detail)

## Example

```bash
agency-novel-switching_log --intent-id $IID …
```
