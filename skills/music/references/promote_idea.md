<!-- agency-generated: v1 -->
# music.promote_idea

Promote an Idea to an Album, recording the Album + PROMOTED_TO edge (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `idea_id, artist, title, genre, type.` |  |  |

## Returns

``{idea_id, album_id, album_slug, status}``.

## Chain-next

``music.conceptualize`` to draft the album concept.

## Details

(no further detail)

## Example

```bash
agency-music-promote_idea --intent-id $IID …
```
