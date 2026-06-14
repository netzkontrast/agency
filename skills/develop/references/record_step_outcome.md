<!-- agency-generated: v1 -->
# develop.record_step_outcome

Mark a PlanStep's execution outcome (Spec 287).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `step_id (from ``draft_plan``), outcome, evidence.` |  |  |

## Returns

``{step_id, state}`` — or ``{error}`` for a bad outcome / unknown step.

## Chain-next

``plan_status(plan_id)`` to roll up; ``delegate.dispatch_decision`` before the next step.

## Details

``outcome`` ∈ {done, blocked, skipped}. Bi-temporal update of the step's ``state`` + ``evidence`` (a new revision, not a destructive overwrite).

## Example

```bash
agency-develop-record_step_outcome --intent-id $IID …
```
