<!-- agency-generated: v1 -->
# loop.advance

Advance the loop ONE transition — the in-session walk step (366).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `loop_id (str), artefact (str — the drafted plan/delivery), judge_output (str — a judge member's verdict), criteria_cwd (str).` |  |  |

## Returns

``{state, decision, stop_reason?, review?}``.

## Chain-next

loop.advance again, or loop.compile when completed.

## Details

(no further detail)

## Example

```bash
agency-loop-advance --intent-id $IID …
```
