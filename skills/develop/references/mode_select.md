<!-- agency-generated: v1 -->
# develop.mode_select

Switch session mode + record a ModeShift node (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session_lifecycle_id, new_mode (one of ``SESSION_MODE``), reason.` |  |  |

## Returns

``{from_mode, to_mode, mode_shift_id}``.

## Chain-next

the walkable skill for the new mode.

## Details

(no further detail)

## Example

```bash
agency-develop-mode_select --intent-id $IID …
```
