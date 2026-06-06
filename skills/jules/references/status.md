<!-- agency-generated: v1 -->
# jules.status

Read a session's full state from the backend.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session (sid).` |  |  |

## Returns

the backend's full state dict (state, url, plan, outputs, …).

## Chain-next

``jules.verify(state=, branch=)`` to confirm push.

## Details

The trimmed `{state, url}` shape was dropping 5 fields the watcher + recovery flow need (R2 audit fix; spec 012 Phase 5).

## Example

```bash
agency-jules-status --intent-id $IID …
```
