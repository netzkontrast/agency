<!-- agency-generated: v1 -->
# prompt.audit

General-case reader-test simulation for any prompt (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `prompt_body, min_score.` |  |  |

## Returns

``{clarity_score, status, findings}``.

## Chain-next

revise + re-audit; or ``prompt.audit_gate`` to gate.

## Details

(no further detail)

## Example

```bash
agency-prompt-audit --intent-id $IID …
```
