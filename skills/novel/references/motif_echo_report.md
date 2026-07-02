<!-- agency-generated: v1 -->
# novel.motif_echo_report

Per-scene echo counts + per-motif trail (transform); flags scenes over the cap (stacking = allegory).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{over_cap: [{scene_id, count, cap}], trails: {slug: [chapter, …]}}``.

## Chain-next

thin the over-cap scenes to one echo.

## Details

(no further detail)

## Example

```bash
agency-novel-motif_echo_report --intent-id $IID …
```
