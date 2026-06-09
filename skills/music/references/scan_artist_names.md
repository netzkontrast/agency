<!-- agency-generated: v1 -->
# music.scan_artist_names

Scan for accidental artist-name drops against the blocklist (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lyrics, allow (allowlist of explicitly permitted artist mentions).` |  |  |

## Returns

``{hits: [{name, severity, fix}], count}``.

## Chain-next

replace flagged names or extend the allowlist.

## Details

(no further detail)

## Example

```bash
agency-music-scan_artist_names --intent-id $IID …
```
