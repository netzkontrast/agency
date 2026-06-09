<!-- agency-generated: v1 -->
# music.resume_session

Restore the last-album context via the StateDriver (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `none.` |  |  |

## Returns

``{session: {last_album?, last_track?, last_phase?, pending_actions?}}``.

## Chain-next

``music.album_progress`` on ``session.last_album`` if set.

## Details

(no further detail)

## Example

```bash
agency-music-resume_session --intent-id $IID …
```
