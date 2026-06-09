<!-- agency-generated: v1 -->
# music.capture_idea

Capture a creative idea (effect) — records an ``Idea`` graph node (provenance) and persists it via the StateDriver.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `text.` |  |  |

## Returns

``{idea_id, text}``.

## Chain-next

``music.conceptualize`` when an idea grows into an album.

## Details

(no further detail)

## Example

```bash
agency-music-capture_idea --intent-id $IID …
```
