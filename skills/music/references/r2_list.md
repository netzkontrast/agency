<!-- agency-generated: v1 -->
# music.r2_list

List published assets by key prefix (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `prefix.` |  |  |

## Returns

``{prefix, objects: [{key, bytes}], count}``.

## Chain-next

``music.r2_delete`` for cleanup.

## Details

(no further detail)

## Example

```bash
agency-music-r2_list --intent-id $IID …
```
