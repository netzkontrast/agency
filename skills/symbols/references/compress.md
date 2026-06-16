<!-- agency-generated: v1 -->
# symbols.compress

Substitute known phrases with symbols — dense, decidable (Spec 300).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `text (str).` |  |  |

## Returns

``{compressed, original_tokens, compressed_tokens, reduction}`` (reduction = fraction of tokens saved).

## Chain-next

symbols.expand to restore prose.

## Details

(no further detail)

## Example

```bash
agency-symbols-compress --intent-id $IID …
```
