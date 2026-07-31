<!-- agency-generated: v1 -->
# novel.list_canon_proposals

List CanonProposals for a novel (transform), optionally filtered by status / scope.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, status (optional — one of PROPOSAL_STATUS), scope (optional exact filter).` |  |  |

## Returns

``{proposals: [{proposal_id, scope, tier, status, proposed_by, decided_by, lock_id}], count}``.

## Chain-next

``novel.approve_canon`` on the open ones.

## Details

(no further detail)

## Example

```bash
agency-novel-list_canon_proposals --intent-id $IID …
```
