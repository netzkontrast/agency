<!-- agency-generated: v1 -->
# thinking.second_order

Trace consequences N steps downstream (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `subject, n_steps (default 3).` |  |  |

## Returns

``{method, subject, n_steps, steps, output_schema}``.

## Chain-next

``thinking.tradeoffs`` if multiple consequence chains compete.

## Details

(no further detail)

## Example

```bash
agency-thinking-second_order --intent-id $IID …
```
