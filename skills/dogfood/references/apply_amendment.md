<!-- agency-generated: v1 -->
# dogfood.apply_amendment

Render a ProposalPayload as a unified diff, recorded as a provenance Artefact.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `payload (dict — ProposalPayload schema; see Plan/150), dry_run (bool — default True; False requires ``confirm_token`` to match the payload id-hash), confirm_token (str — opt-in live-write gate).` |  |  |

## Returns

``{diff, artefact_id, written_path?}``. Failure modes: ``AMENDMENT_BAD_SPEC`` (no such spec dir), ``AMENDMENT_NO_SOURCE`` (citations empty), ``AMENDMENT_VAGUE`` (rationale < 40 chars), ``AMENDMENT_UNCONFIRMED`` (live write requested, confirm_token does not match the payload id-hash).

## Chain-next

review the diff, then re-call with ``dry_run=False`` + ``confirm_token`` to write the amendment.

## Details

v1 always renders the diff and writes an `Artefact(kind="amendment-proposal")` with PRODUCES_FROM edges to every cited Reflection so a reviewer can trace any amendment back to its source observations (the provenance moat invariant).

## Example

```bash
agency-dogfood-apply_amendment --intent-id $IID …
```
