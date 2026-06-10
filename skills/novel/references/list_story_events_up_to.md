<!-- agency-generated: v1 -->
# novel.list_story_events_up_to

Story-time slice: events with ``when_story`` ≤ this scene's anchor (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id.` |  |  |

## Returns

``{anchor_when, events: [{event_id, label, when_story}]}``.

## Chain-next

``prompt.assemble_scene_brief`` consumes this for the continuity section.

## Details

The scene's anchor is the ``when_story`` of any StoryTimeEvent the scene HAPPENS_AT. If the scene has multiple, takes the latest. No anchor → empty list (the scene has no story-time reference frame yet).

## Example

```bash
agency-novel-list_story_events_up_to --intent-id $IID …
```
