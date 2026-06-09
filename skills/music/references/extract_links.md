<!-- agency-generated: v1 -->
# music.extract_links

Extract URLs from text via simple regex (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `text.` |  |  |

## Returns

``{urls, count}``.

## Chain-next

``music.verify_streaming`` to check each.

## Details

Driver-free — uses stdlib re. Filters obvious SSRF risks (rejects javascript:/file:/data: schemes).

## Example

```bash
agency-music-extract_links --intent-id $IID …
```
