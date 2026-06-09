<!-- agency-generated: v1 -->
# music.validate_album

Validate album file presence + mirror-path consistency via StateDriver (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album (slug).` |  |  |

## Returns

``{album, files_present, mirror_paths_ok, issues}``.

## Chain-next

``music.validate_sections`` for per-track structure.

## Details

(no further detail)

## Example

```bash
agency-music-validate_album --intent-id $IID …
```
