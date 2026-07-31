<!-- agency-generated: v1 -->
# novel.anchor_beat

Map a manuscript scene to a beat: ``FULFILS`` edge + the expectation's ``scene_id`` (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, beat_slug (from the applied template), scene_id.` |  |  |

## Returns

``{novel_id, beat_slug, scene_id, anchored}``.

## Chain-next

``novel.structure_position_report`` once several beats are anchored.

## Details

(no further detail)

## Example

```bash
agency-novel-anchor_beat --intent-id $IID …
```
