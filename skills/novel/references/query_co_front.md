<!-- agency-generated: v1 -->
# novel.query_co_front

Scenes where two system alters co-front (transform): every scene whose cast holds ≥ 2 alters of this system, filtered by pair kind — ``max`` (max-intensity conflict pairs; the canon violation), ``adjacent`` (any conflict edge), ``any`` (all pairs).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `system_id, pair_kind (max|adjacent|any).` |  |  |

## Returns

``{occurrences: [{scene_id, alter_ids, pair_kind, violates_canon}], system_id}``.

## Chain-next

split the violating scenes (the KP discipline) or pass allow_max_pair explicitly at compose time.

## Details

(no further detail)

## Example

```bash
agency-novel-query_co_front --intent-id $IID …
```
