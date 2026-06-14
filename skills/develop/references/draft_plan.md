<!-- agency-generated: v1 -->
# develop.draft_plan

Author a bite-sized plan as graph provenance (Spec 287; rule 2).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `title, steps (JSON list or newlines).` |  |  |

## Returns

``{plan_id, step_ids, count}``.

## Chain-next

walk ``plan-execute``, or sign off then ``record_step_outcome`` per step + ``plan_status`` to roll up.

## Details

``steps`` is a JSON array of step descriptions OR a newline-separated list. Mints a ``Plan{title}`` + one ``PlanStep{index, description, state:pending}`` per step, the Plan SERVING the intent and ``HAS_STEP`` each PlanStep. The plan markdown is rendered on demand from these nodes — never a parsed file. The ``plan-execute`` discipline's draft-plan phase binds to this verb.

## Example

```bash
agency-develop-draft_plan --intent-id $IID …
```
