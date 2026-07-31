<!-- agency-generated: v1 -->
# novel.structure_position_report

Target vs actual manuscript position per anchored beat (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{beats: [{beat_slug, target_position, actual_position, out_of_position}]}``.

## Chain-next

revise chapter order / re-anchor, then re-run.

## Details

``actual_position`` uses cumulative word count when chapters carry bodies, else the chapter midpoint fraction (OQ3). A beat drifting beyond ``POSITION_TOLERANCE`` is flagged ``out_of_position``.

## Example

```bash
agency-novel-structure_position_report --intent-id $IID …
```
