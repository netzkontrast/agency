<!-- agency-generated: v1 -->
# jules.approve_plan

Approve a plan in AWAITING_PLAN_APPROVAL — the one state that times out.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session (sid).` |  |  |

## Returns

backend response (typically ``{state: WORKING}`` after).

## Chain-next

poll ``jules.status(session=)`` until COMPLETED / FAILED.

## Details

(no further detail)

## Example

```bash
agency-jules-approve_plan --intent-id $IID …
```
