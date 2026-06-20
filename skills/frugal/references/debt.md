<!-- agency-generated: v1 -->
# frugal.debt

Harvest deliberate ``frugal:``/``ponytail:`` shortcut markers into a debt ledger — each a ``DebtMarker`` node SERVING the intent, so "what did we defer" is a query, not a re-grep (the substrate's edge over the JS original).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `paths (str — optional path filter; empty = all tracked source).` |  |  |

## Returns

token-bounded ``{markers, no_trigger, top: [...]}`` — the FULL ledger is in the graph (DebtMarker nodes); the wire caps at the top-N (Spec 348-review Sev3#5: full capture, bounded return).

## Chain-next

query the DebtMarker nodes for the full ledger.

## Details

(no further detail)

## Example

```bash
agency-frugal-debt --intent-id $IID …
```
