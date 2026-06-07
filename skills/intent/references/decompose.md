<!-- agency-generated: v1 -->
# intent.decompose

Decompose a goal into MECE sub-problems — the structured break-down method.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `subject (defaults to the serving intent's deliverable).` |  |  |

## Returns

``{method, subject, steps, output}`` — a scaffold to fill in.

## Chain-next

``intent.assumptions`` on the riskiest sub-problem.

## Details

(no further detail)

## Example

```bash
agency-intent-decompose --intent-id $IID …
```
