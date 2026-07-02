<!-- agency-generated: v1 -->
# novel.route_scene_storyform

Route a scene between the live storyforms (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id, set_id, primary_role, mode (hard | soft), secondary_role (required + distinct for soft).` |  |  |

## Returns

``{scene_id, mode, routed_storyforms}``.

## Chain-next

``novel.bridge_frequency_report(novel_id)``.

## Details

(no further detail)

## Example

```bash
agency-novel-route_scene_storyform --intent-id $IID …
```
