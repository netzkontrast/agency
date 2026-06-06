<!-- agency-generated: v1 -->
# jules.status_all

Paginated, grouped-by-state listing of every session on the account.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `page_size (int), max_pages (int).` |  |  |

## Returns

``{by_state, totals, total, truncated}``.

## Chain-next

``jules.approve_awaiting`` for AWAITING_PLAN_APPROVAL group.

## Details

Operational hygiene (lesson-15 §3); the watcher uses it to seed the registry.

## Example

```bash
agency-jules-status_all --intent-id $IID …
```
