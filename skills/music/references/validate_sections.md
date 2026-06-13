<!-- agency-generated: v1 -->
# music.validate_sections

Validate lyric section structure across an album (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, lyrics (optional — empty = read all album tracks).` |  |  |

## Returns

``{album, ok, findings, track_count}``.

## Chain-next

revise bad-tagged sections.

## Details

Delegates to the 095 TextDriver `validate_sections`. Aggregates findings across all track bodies if `lyrics` is empty. ``music_text`` is decorator-injected (always required). The ``music_state`` driver is fetched inline only on the empty-lyrics branch (a conditional second dependency), so it stays on the raw ``_require_drv`` 2-tuple helper.

## Example

```bash
agency-music-validate_sections --intent-id $IID …
```
