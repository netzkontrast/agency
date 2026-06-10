<!-- agency-generated: v1 -->
# novel.reveal_in_scene

Add the REVEALED_IN edge (event disclosed by this scene) (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `event_id (existing StoryTimeEvent), scene_id (existing Scene).` |  |  |

## Returns

``{event_id, scene_id}``.

## Chain-next

``novel.list_reveals_in(scene_id)`` to verify.

## Details

(no further detail)

## Example

```bash
agency-novel-reveal_in_scene --intent-id $IID …
```
