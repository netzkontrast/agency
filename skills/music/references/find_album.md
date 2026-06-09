<!-- agency-generated: v1 -->
# music.find_album

Find albums by slug / fuzzy match via the StateDriver (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `query (slug-exact wins; substring then; ``""`` returns all).` |  |  |

## Returns

``{albums: […], count, query}``.

## Chain-next

``music.album_progress`` on a found slug.

## Details

(no further detail)

## Example

```bash
agency-music-find_album --intent-id $IID …
```
