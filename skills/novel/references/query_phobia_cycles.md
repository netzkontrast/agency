<!-- agency-generated: v1 -->
# novel.query_phobia_cycles

Find PHOBIA_OF cycles in the conflict matrix (transform) — pure edge walk.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `system_id.` |  |  |

## Returns

``{cycles: [{alter_ids, length, weight}], system_id}`` — ids only, never names (recognition discipline).

## Chain-next

``novel.conflict_matrix_report`` for the cell detail.

## Details

(no further detail)

## Example

```bash
agency-novel-query_phobia_cycles --intent-id $IID …
```
