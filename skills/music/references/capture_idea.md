<!-- agency-generated: v1 -->
# music.capture_idea

Capture a creative idea (effect) — record an Idea node, persist via StateDriver.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `text.` |  |  |

## Returns

``{idea_id, text, status}``.

## Chain-next

``music.promote_idea`` when an idea grows into an album.

## Details

(no further detail)

## Example

```bash
agency-music-capture_idea --intent-id $IID …
```
