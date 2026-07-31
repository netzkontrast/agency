<!-- agency-generated: v1 -->
# novel.story_time_query

The continuity scan (transform): every StoryTimeEvent + beat, and SURFACED temporal contradictions — an event whose scene-order (HAPPENS_AT) contradicts its ``when_story`` ordering is returned in ``contradictions``, never silently sorted around.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{events, beats, contradictions: [{earlier, later, reason}], coverage}`` — coverage 1.0 on an empty scope (vacuous truth).

## Chain-next

fix the contradicting when_story anchors; re-run.

## Details

(no further detail)

## Example

```bash
agency-novel-story_time_query --intent-id $IID …
```
