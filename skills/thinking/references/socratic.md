<!-- agency-generated: v1 -->
# thinking.socratic

Five-whys-deeper Socratic questioning (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `subject, n_questions (default 5; the "five whys" depth).` |  |  |

## Returns

``{method, subject, n_questions, steps, output_schema}``.

## Chain-next

``thinking.assumptions`` on the surfaced root.

## Details

Recursively asks "why" / "what does that assume" to surface the root assumption.

## Example

```bash
agency-thinking-socratic --intent-id $IID …
```
