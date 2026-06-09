<!-- agency-generated: v1 -->
# prompt.engineer

Render a PromptInstance inside a token budget (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `builder_kind (free-form slug), context, constraints, max_tokens.` |  |  |

## Returns

``{result, artefact}`` prompt-instance artefact.

## Chain-next

``prompt.token_budget_gate`` to gate the lifecycle.

## Details

Composes context + constraints into a structured prompt body using the canonical layout: # <builder_kind> prompt ## Context <context> ## Constraints <constraints> Records a PromptInstance node + body. Refuses to produce a body that exceeds ``max_tokens`` (returns INVALID_ARGUMENT instead — the caller revises before re-engineering).

## Example

```bash
agency-prompt-engineer --intent-id $IID …
```
