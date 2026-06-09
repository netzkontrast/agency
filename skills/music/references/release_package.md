<!-- agency-generated: v1 -->
# music.release_package

Record a release package — gathers all release artefact paths (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, assets (list of artefact keys / paths to bundle).` |  |  |

## Returns

``{result, artefact}`` promo-album-package artefact.

## Chain-next

``music.release-publish`` skill walk to upload + announce.

## Details

(no further detail)

## Example

```bash
agency-music-release_package --intent-id $IID …
```
