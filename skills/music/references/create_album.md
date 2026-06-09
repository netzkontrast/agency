<!-- agency-generated: v1 -->
# music.create_album

Create an album root + render the canonical templates (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `artist, title, genre, type (default ``thematic``).` |  |  |

## Returns

``{album_id, album_slug, album_root, artist_seeded, title}``.

## Chain-next

``music.create_track`` for each track in the tracklist.

## Details

Records an ``Album`` graph node, calls StateDriver.create_album_root for the disk layout (production); the README is rendered from the bitwize- ported ``album`` template (Spec 094 §"Template porting"). Optional ``artist`` page renders on first album for this artist.

## Example

```bash
agency-music-create_album --intent-id $IID …
```
