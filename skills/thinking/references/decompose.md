<!-- agency-generated: v1 -->
# thinking.decompose

MECE sub-problem decomposition (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `subject (defaults to the serving intent's deliverable).` |  |  |

## Returns

``{method, subject, steps, output_schema}``.

## Chain-next

``thinking.assumptions`` on the riskiest sub-problem.

## Details

(no further detail)

## Example

```bash
agency-thinking-decompose --intent-id $IID …
```
