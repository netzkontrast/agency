<!-- agency-generated: v1 -->
# music.repetition_gate

Computed cross-track repetition gate (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, tracks (list of lyric bodies).` |  |  |

## Returns

``{gate, passed, evidence}`` or typed GATE_FAILED.

## Chain-next

rewrite the repeated lines on one of the tracks.

## Details

Passes iff no lyric line is repeated across multiple tracks. Records PASSED/BLOCKED_ON on the lifecycle via gate.check.

## Example

```bash
agency-music-repetition_gate --intent-id $IID …
```
