<!-- agency-generated: v1 -->
# workflow.approve_decisions

APPROVE_DECISIONS — phase 11: run `adr.approve` over every decision that `REFINES` the spec (the ADR hinge's human step).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `spec_id, approver (owner identity), override (owner bypass of the automated DoD gate for a skeleton decision).` |  |  |

## Returns

``{spec_id, approved: [{id, approved}], ready}`` — ``ready`` is the post-approval /open→/inprogress predicate.

## Chain-next

workflow.begin_impl(spec_id).

## Details

(no further detail)

## Example

```bash
agency-workflow-approve_decisions --intent-id $IID …
```
