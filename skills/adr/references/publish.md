<!-- agency-generated: v1 -->
# adr.publish

PUBLISH — project a theme to its ``docs/adr/<layer>.md`` FILE: the keep-both file side of `render`.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `theme_id, out (override the theme's path — for tests), apply (write the file; else preview the body).` |  |  |

## Returns

``{theme_id, path, written, content_sha, body}`` or ``{error}``.

## Chain-next

adr.architecture(apply=True) to roll the published ADRs up.

## Details

(no further detail)

## Example

```bash
agency-adr-publish --intent-id $IID …
```
