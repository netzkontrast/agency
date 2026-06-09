<!-- agency-generated: v1 -->
# prompt.audit_gate

Computed audit gate — passes iff clarity_score ≥ min_score (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, prompt_body, min_score.` |  |  |

## Returns

``{gate, passed, score, status}`` or typed GATE_FAILED.

## Chain-next

on failure, revise + re-audit.

## Details

(no further detail)

## Example

```bash
agency-prompt-audit_gate --intent-id $IID …
```
