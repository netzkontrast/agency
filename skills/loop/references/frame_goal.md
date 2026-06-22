<!-- agency-generated: v1 -->
# loop.frame_goal

Frame a loop goal as a root Intent (the goal IS an Intent, 363).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `statement (str), definition_of_done (str), deliverable (str), context_sources (list of {file}|{cmd` |  | [argv]} — argv-safe). |

## Returns

``{goal_id, context_sources}``.

## Chain-next

loop.critique_goal(goal_id) then loop.open(goal_id).

## Details

(no further detail)

## Example

```bash
agency-loop-frame_goal --intent-id $IID …
```
