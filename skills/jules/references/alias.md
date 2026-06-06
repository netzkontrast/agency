<!-- agency-generated: v1 -->
# jules.alias

Read or upsert a stable alias for a Jules sid.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name (alias slug), session (sid — empty = look up).` |  |  |

## Returns

``{name, session}`` on hit; ``{error}`` on lookup miss.

## Chain-next

``jules.status(session=)`` once resolved.

## Details

Stored as a ``JulesAlias`` node in the bi-temporal graph (no parallel sessions.json per the canon CORE.md:38-45).

## Example

```bash
agency-jules-alias --intent-id $IID …
```
