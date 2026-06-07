<!-- agency-generated: v1 -->
# intent.second_order

Trace second- and third-order consequences — 'and then what?' past the first effect.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `subject (the action/decision; defaults to the intent).` |  |  |

## Returns

a scaffold that pushes past the immediate effect.

## Chain-next

feed the downstream effects into ``intent.tradeoffs``.

## Details

(no further detail)

## Example

```bash
agency-intent-second_order --intent-id $IID …
```
