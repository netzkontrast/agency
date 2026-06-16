<!-- agency-generated: v1 -->
# document.restore_session

Restore a complete session from the Session Graph (Spec 292).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session_id (str — the Claude Code session id, bare or ``session` |  | ``-prefixed). |

## Returns

``{session_id, status, event_count, events, document_id}``.

## Chain-next

``document.reopen`` the document_id's file to read the four concepts, or ``dogfood.replay_events`` for detail.

## Details

The hooks build a `Session` node (keyed by Claude Code's session_id) that every Event links ``IN_SESSION``, with the session-end Document attached. This verb walks that node to reconstruct the whole session from the graph alone — its event timeline + the archived four-concept Document — so a session is never lost when its process ends.

## Example

```bash
agency-document-restore_session --intent-id $IID …
```
