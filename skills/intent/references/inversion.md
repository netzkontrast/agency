<!-- agency-generated: v1 -->
# intent.inversion

Invert the goal — ask what would GUARANTEE failure, then avoid exactly that.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `subject (defaults to the serving intent).` |  |  |

## Returns

a scaffold of failure-guarantees to design against.

## Chain-next

``intent.premortem`` for likelihoods.

## Details

(no further detail)

## Example

```bash
agency-intent-inversion --intent-id $IID …
```
