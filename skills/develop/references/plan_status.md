<!-- agency-generated: v1 -->
# develop.plan_status

Roll up a Plan's steps + completion (Spec 287) — the render-on-demand read side (rule 2).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `plan_id.` |  |  |

## Returns

``{title, status, steps:[{index, description, state}], complete}`` — ``complete`` is True iff every step is done|skipped. ``{error}`` for an unknown plan.

## Chain-next

render the plan markdown from this, or continue the walk.

## Details

(no further detail)

## Example

```bash
agency-develop-plan_status --intent-id $IID …
```
