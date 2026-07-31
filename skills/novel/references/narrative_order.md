<!-- agency-generated: v1 -->
# novel.narrative_order

The narrative order DERIVED as a typed path over PRECEDES (transform) — a topological order of the beat DAG, never an ad-hoc property sort.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{order: [beat_id], beats: [{beat_id, label, scene_id}], edges_traversed}`` — ``order`` is the id path (Spec 238), ``beats`` the enriched Spec-128 reading-order shape.

## Chain-next

``novel.story_time_query`` for the contradiction scan.

## Details

(no further detail)

## Example

```bash
agency-novel-narrative_order --intent-id $IID …
```
