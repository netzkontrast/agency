<!-- agency-generated: v1 -->
# novel.record_story_event

Mint a StoryTimeEvent + optional HAPPENS_AT edge from a scene (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, label (short event name), when_story (sortable string), scene_id (optional — when supplied, mints Scene-HAPPENS_AT->Event edge).` |  |  |

## Returns

``{event_id, label, when_story, scene_id?}``.

## Chain-next

``novel.reveal_in_scene`` for foreshadow/payoff.

## Details

``when_story`` is a plain string by design (Open Q1) — the author owns sortability. Lexicographic sort is the slice contract for ``list_story_events_up_to``.

## Example

```bash
agency-novel-record_story_event --intent-id $IID …
```
