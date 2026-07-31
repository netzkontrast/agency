<!-- agency-generated: v1 -->
# novel.approve_canon

Decide a CanonProposal (effect) — approval is the ONLY path that mints an approval-provenance Lock.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `proposal_id, approver (who decides — required), decision (approve | reject), reason (required for reject), approver_kind (human | managed_agent — the latter denied).` |  |  |

## Returns

``{proposal_id, decision, lock_id, decided_by, decided_at, dogfood_reflection_id, idempotent}``.

## Chain-next

``novel.lock_index`` — the new Lock is live; or re-propose after a rejection.

## Details

(no further detail)

## Example

```bash
agency-novel-approve_canon --intent-id $IID …
```
