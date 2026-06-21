<!-- agency-generated: v1 -->
# adr.dod_check

DOD_CHECK — run the ported SPEC-001-E Definition-of-Done criteria over a Decision (pure compute; never flips status).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `decision_id (str).` |  |  |

## Returns

``{decision_id, criteria: [{id, criterion, mode, passed, severity, msg}], auto_passed, human_pending: [id…], score}`` — ``auto_passed`` is True iff every ``error``-severity auto/partial check passes; ``score`` is the SPEC-001-E weighted fraction (surfaced, NOT gating — rule 8). Or ``{error}`` if absent.

## Chain-next

adr.approve(decision_id, approver=…) to clear the gate.

## Details

(no further detail)

## Example

```bash
agency-adr-dod_check --intent-id $IID …
```
