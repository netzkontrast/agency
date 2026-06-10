<!-- agency-generated: v1 -->
# novel.narrative_order

Topo-sort over PRECEDES; canonical narrative reading order (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{beats: [{beat_id, label, scene_id}]}`` ordered so every predecessor appears before its successor.

## Chain-next

author's checklist for the manuscript's narrative spine.

## Details

(no further detail)

## Example

```bash
agency-novel-narrative_order --intent-id $IID …
```
