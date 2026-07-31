<!-- agency-generated: v1 -->
# novel.conflict_matrix_report

Render the full conflict matrix (transform): all typed phobia cells, counts per vector, and the max-intensity pairs that must never co-front a scene without a voice-collision warning.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `system_id.` |  |  |

## Returns

``{alters, cells, max_pairs, by_vector}``.

## Chain-next

consult ``max_pairs`` before staging a co-front scene.

## Details

(no further detail)

## Example

```bash
agency-novel-conflict_matrix_report --intent-id $IID …
```
