<!-- agency-generated: v1 -->
# prompt.token_budget_gate

Computed token-budget gate — passes iff approx_tokens ≤ max_tokens (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, prompt_body, max_tokens.` |  |  |

## Returns

``{gate, passed, tokens, max_tokens}`` or typed GATE_FAILED.

## Chain-next

on failure, revise + re-engineer + re-gate.

## Details

(no further detail)

## Example

```bash
agency-prompt-token_budget_gate --intent-id $IID …
```
