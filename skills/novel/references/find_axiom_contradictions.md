<!-- agency-generated: v1 -->
# novel.find_axiom_contradictions

Decidable axiom-contradiction scan + emit CONTRADICTS edges (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `world_id.` |  |  |

## Returns

``{passed, contradictions: [{a_id, b_id, a_text, b_text}]}``.

## Chain-next

walk pairs; refine wording; rerun.

## Details

Per Open Q2 (resolved as v1 decidable): flags axiom pairs whose bodies share ≥ 2 motif words AND one carries a negation marker the other lacks (``not``, ``never``, ``no``). The judgement pass (full red_team) is a future xcap to ``thinking.red_team``.

## Example

```bash
agency-novel-find_axiom_contradictions --intent-id $IID …
```
