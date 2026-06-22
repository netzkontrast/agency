<!-- agency-generated: v1 -->
# loop.critique_goal

Coach a loop goal against goal-rubric.md — advisory, never blocks (363).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `goal_id (str — the goal Intent id).` |  |  |

## Returns

``{findings, clarity, ok, rubric_source}``.

## Chain-next

re-frame on a failing dimension, or loop.open.

## Details

(no further detail)

## Example

```bash
agency-loop-critique_goal --intent-id $IID …
```
