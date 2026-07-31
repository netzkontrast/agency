<!-- agency-generated: v1 -->
# novel.record_alter_conflict

Mint the ``PHOBIA_OF`` conflict-matrix edge a→b (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `alter_a, alter_b (distinct), vector (anp-ep|anp-anp|ep-ep| mirror), intensity (max|phobic-avoidance|friction|ambivalent), rationale (freeform why).` |  |  |

## Returns

``{a, b, vector, intensity}``.

## Chain-next

``novel.conflict_matrix_report(system_id)``.

## Details

(no further detail)

## Example

```bash
agency-novel-record_alter_conflict --intent-id $IID …
```
