<!-- agency-generated: v1 -->
# intent.premortem

Premortem — assume the goal FAILED, reason backward to causes + mitigations.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `subject (defaults to the serving intent).` |  |  |

## Returns

a scaffold that elicits specific (not generic) failure modes.

## Chain-next

fold the top mitigations into the plan.

## Details

(no further detail)

## Example

```bash
agency-intent-premortem --intent-id $IID …
```
