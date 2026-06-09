<!-- agency-generated: v1 -->
# music.get_reference

Read a bundled reference / data file by slug (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `slug (path or filename under data/<kind>/), kind (default ``reference``).` |  |  |

## Returns

``{kind, slug, body}``.

## Chain-next

feed the body into a verb that needs the doctrine context.

## Details

Resolves from ``agency/capabilities/music/data/<kind>/<slug>``. ``kind`` defaults to ``reference`` (the 50 bitwize docs ported in Spec 094). Pass ``kind="genres"`` to read a genre file.

## Example

```bash
agency-music-get_reference --intent-id $IID …
```
