<!-- agency-generated: v1 -->
# doctrine.resolve

Adjudicate two conflicting concerns by the conflict hierarchy (safety > correctness > maintainability > speed) — read-only (Spec 303).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `a (str — one concern), b (str — the other).` |  |  |

## Returns

``{winner, winner_category, loser, loser_category, tie, rationale}``.

## Chain-next

gate.adjudicate wraps this; doctrine.cite the winning rule.

## Details

Each side (a rule name, a category, or free-text like 'ship fast') is classified into a hierarchy category; the higher-ranked category wins. Equal categories are a tie (no winner — the caller decides).

## Example

```bash
agency-doctrine-resolve --intent-id $IID …
```
