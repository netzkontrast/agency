<!-- agency-generated: v1 -->
# adr.render

RENDER — project a theme's **live** decisions into a markdown body and stamp the theme ``Document``'s ``content_sha`` (graph-side projection; the file round-trip is `document.sync`'s job, keep-both — Spec 292).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `theme_id (str).` |  |  |

## Returns

``{id, path, content_sha, active, superseded, body}`` or ``{error}``.

## Chain-next

document.sync(path) to round-trip the body to disk.

## Details

(no further detail)

## Example

```bash
agency-adr-render --intent-id $IID …
```
