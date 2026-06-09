<!-- agency-generated: v1 -->
# music.catalogue_status

Read track statuses from the catalogue DB via the DBDriver (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album.` |  |  |

## Returns

``{tracks: [{slug, status}]}``.

## Chain-next

gate on all-tracks-mastered before release.

## Details

(no further detail)

## Example

```bash
agency-music-catalogue_status --intent-id $IID …
```
