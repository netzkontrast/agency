<!-- agency-generated: v1 -->
# novel.propose_canon

Open a CanonProposal — the reviewed path toward a Lock (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, scope (what the canon claim governs), payload (the claim, dict), rationale, tier (V | K | author), evidence (approved lock id — required for K), proposed_by, author_override (required True for tier=author), supersedes_lock (optional active Lock id).` |  |  |

## Returns

``{proposal_id, scope, tier, status, intent_id}``.

## Chain-next

``novel.approve_canon(proposal_id, approver, decision)``.

## Details

The source-hierarchy gate runs at propose-time: a ``tier="K"`` proposal MUST cite an APPROVED lock as ``evidence``; ``tier= "author"`` requires ``author_override=True``. A non-dict payload is rejected (schema mismatch is signal, not noise). Every proposal mints a serving sub-Intent (Spec 176 — the approval request survives the proposal's lifecycle). ``supersedes_lock`` names an active Lock this proposal, once approved, will supersede.

## Example

```bash
agency-novel-propose_canon --intent-id $IID …
```
