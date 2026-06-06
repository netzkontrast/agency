<!-- agency-generated: v1 -->
# jules.resolve_source

Resolve `owner/repo` to the opaque `sources/<id>` the API expects.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `owner (str), repo (str).` |  |  |

## Returns

``{source_id, owner, repo}`` or ``{error}`` on miss.

## Chain-next

pass ``source_id`` (or ``owner/repo``) to ``jules.dispatch``.

## Details

The composition is undocumented; must list-and-match. Read-only.

## Example

```bash
agency-jules-resolve_source --intent-id $IID …
```
