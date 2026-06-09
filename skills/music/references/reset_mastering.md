<!-- agency-generated: v1 -->
# music.reset_mastering

Revert all master/polish state for an album (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album (slug).` |  |  |

## Returns

``{album, reset}``.

## Chain-next

re-run ``music.polish_and_master_album``.

## Details

(no further detail)

## Example

```bash
agency-music-reset_mastering --intent-id $IID …
```
