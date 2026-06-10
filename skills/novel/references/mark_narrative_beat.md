<!-- agency-generated: v1 -->
# novel.mark_narrative_beat

Mint a NarrativeBeat + optional PRECEDES edge from a predecessor (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id, beat_label (e.g. "opening-image" or "inciting-incident"), predecessor_id (optional — links the new beat into the narrative-order DAG).` |  |  |

## Returns

``{beat_id, scene_id, label}``.

## Chain-next

``novel.narrative_order(novel_id)`` to read topo-sort.

## Details

(no further detail)

## Example

```bash
agency-novel-mark_narrative_beat --intent-id $IID …
```
