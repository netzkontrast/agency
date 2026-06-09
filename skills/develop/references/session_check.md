<!-- agency-generated: v1 -->
# develop.session_check

Read the current SessionLifecycle state (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session_lifecycle_id (defaults to the most recent SessionLifecycle SERVING the current intent).` |  |  |

## Returns

``{session_lifecycle_id, mode, status, mode_history}``.

## Chain-next

``develop.mode_select`` to switch modes.

## Details

(no further detail)

## Example

```bash
agency-develop-session_check --intent-id $IID …
```
