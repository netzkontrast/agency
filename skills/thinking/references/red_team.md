<!-- agency-generated: v1 -->
# thinking.red_team

Adversarial review — adopt an attacker's stance + find failure paths (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `subject, n_attacks (default 5).` |  |  |

## Returns

``{method, subject, n_attacks, steps, output_schema}``.

## Chain-next

prioritize the highest-severity attack + design mitigation.

## Details

Distinct from steelman: steelman finds the strongest argument AGAINST your position; red_team finds the strongest path to your SYSTEM's failure.

## Example

```bash
agency-thinking-red_team --intent-id $IID …
```
