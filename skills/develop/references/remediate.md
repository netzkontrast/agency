<!-- agency-generated: v1 -->
# develop.remediate

Apply the remedy phase of a prior review — safe fixes auto-applied, risky ones reported as gated (MUTATES → role=effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `review_id (from a prior develop.review or analyze.review call; optional — when absent, returns empty applied/gated lists), apply_safe (bool — auto-apply safe remedies, default True).` |  |  |

## Returns

{review_id, applied:[...], gated:[...]}.

## Chain-next

confirm a risky gated remedy, then commit.

## Details

Safe remedies (mechanical + local) are applied when apply_safe=True. Risky remedies (structural) are reported in gated:[...] and require explicit user confirmation. Under the headless/CI actor (analyze.review), risky remedies are auto-declined — never paused (Cockburn fix).

## Example

```bash
agency-develop-remediate --intent-id $IID …
```
