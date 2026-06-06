<!-- agency-generated: v1 -->
# jules.message

Send a message into a session (feedback / plan-revision / nudge to push).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session (sid), prompt (str — the message body).` |  |  |

## Returns

backend response (typically ``{ok}`` on accept).

## Chain-next

poll ``jules.status(session=)`` — resumption is racy.

## Details

Input only, NOT a control plane. Never use to revive a FAILED session or to cancel one.

## Example

```bash
agency-jules-message --intent-id $IID …
```
