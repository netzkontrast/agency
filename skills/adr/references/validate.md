<!-- agency-generated: v1 -->
# adr.validate

VALIDATE — run the decidable WH(Y) rules over a Decision; return findings + an ``ok`` flag.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `decision_id (str).` |  |  |

## Returns

``{decision_id, findings: [{rule, severity, msg}], ok}`` — ``ok`` is False iff any ``error`` finding fires.

## Chain-next

adr.approve(decision_id) once ok (355, Slice 2).

## Details

Findings: - **WHY-001** (error): every WH(Y) element the Schema requires is present and non-empty (the approval-gating completeness check). - **WHY-003** (error): ``neglected`` documents at least one real alternative (semantic — the ontology cannot catch a non-empty "none"). - **WHY-LEN** (warn): an element exceeds its Schema ``maxLength`` budget.

## Example

```bash
agency-adr-validate --intent-id $IID …
```
