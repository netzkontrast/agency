<!-- agency-generated: v1 -->
# novel.check_reveal_timing

Check one scene against every tier's rule for a fact (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id, fact.` |  |  |

## Returns

``{ok, violations: [{tier, rule_id, floor, chapter}], no_rule?}``.

## Chain-next

move the reveal later, or adjust the rule.

## Details

(no further detail)

## Example

```bash
agency-novel-check_reveal_timing --intent-id $IID …
```
