<!-- agency-generated: v1 -->
# intent.tradeoffs

Build an explicit trade-off matrix — options × criteria — for a decision.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `options (comma-separated; '' → elicit them); criteria (comma-separated; '' → suggest defaults). Defaults the subject to the serving intent.` |  |  |

## Returns

a matrix scaffold + the tie-breaking discipline.

## Chain-next

``intent.steelman`` the option you're about to reject.

## Details

(no further detail)

## Example

```bash
agency-intent-tradeoffs --intent-id $IID …
```
