<!-- agency-generated: v1 -->
# dogfood.record_decision

Bind a decision to the current session (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `subject (what was decided about), decision (the choice), rationale (why), next_action (what follows), session_lifecycle_id (optional — links the DecisionRecord to the session).` |  |  |

## Returns

``{decision_id, subject, decision}``.

## Chain-next

act on `next_action`, or `reflect.note` the rationale.

## Details

Creates a `DecisionRecord` node SERVING the intent. Optionally edges to a SessionLifecycle so the decision history is queryable.

## Example

```bash
agency-dogfood-record_decision --intent-id $IID …
```
