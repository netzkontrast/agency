<!-- agency-generated: v1 -->
# music.pronunciation_gate

Computed pronunciation gate — composes pronunciation + homograph (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, lyrics.` |  |  |

## Returns

``{gate, passed, evidence}`` or typed GATE_FAILED.

## Chain-next

resolve flagged words then re-check.

## Details

Passes iff zero pronunciation findings AND zero homograph findings. Records PASSED/BLOCKED_ON on the lifecycle via gate.check.

## Example

```bash
agency-music-pronunciation_gate --intent-id $IID …
```
