<!-- agency-generated: v1 -->
# music.pending_verifications

Aggregate count of pending claims (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album.` |  |  |

## Returns

``{album, pending_count, by_domain}``.

## Chain-next

``music.verify_sources``.

## Details

(no further detail)

## Example

```bash
agency-music-pending_verifications --intent-id $IID …
```
