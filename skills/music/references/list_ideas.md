<!-- agency-generated: v1 -->
# music.list_ideas

List captured ideas via the StateDriver (transform) — filter by status.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `status (one of ``IDEA_STATUS`` or ``""`` for all).` |  |  |

## Returns

``{ideas: [{idea_id, text, status, …}], count}``.

## Chain-next

``music.promote_idea`` to turn a "new" idea into an album.

## Details

(no further detail)

## Example

```bash
agency-music-list_ideas --intent-id $IID …
```
