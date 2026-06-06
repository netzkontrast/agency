<!-- agency-generated: v1 -->
# jules.approve_awaiting

Bulk-approve every session in AWAITING_PLAN_APPROVAL (up to `limit`).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `limit (int — cap; 0 = all).` |  |  |

## Returns

``{approved, skipped}``.

## Chain-next

poll ``jules.status_all`` until all approved sessions transition to WORKING / COMPLETED.

## Details

The one state with a timeout/discard window; don't let it sit (lesson-15 §6).

## Example

```bash
agency-jules-approve_awaiting --intent-id $IID …
```
