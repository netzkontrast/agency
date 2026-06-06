<!-- agency-generated: v1 -->
# jules.stop

UNSUPPORTED by design: the Jules v1alpha API exposes no cancel/delete/stop.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session (sid).` |  |  |

## Returns

``{error: 'unsupported', session, message}``.

## Chain-next

``jules.message(session=, prompt='please stop')`` or wait for terminal state (COMPLETED / FAILED).

## Details

(no further detail)

## Example

```bash
agency-jules-stop --intent-id $IID …
```
