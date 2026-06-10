<!-- agency-generated: v1 -->
# novel.list_reveals_in

List events this scene discloses (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id.` |  |  |

## Returns

``{reveals: [{event_id, label, when_story}]}``.

## Chain-next

author's checklist for "is the reveal landing here?".

## Details

Walks REVEALED_IN edges incoming on the scene (so an Event points to a Scene as its reveal point).

## Example

```bash
agency-novel-list_reveals_in --intent-id $IID …
```
