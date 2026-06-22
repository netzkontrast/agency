<!-- agency-generated: v1 -->
# loop.compile

Resolve a loop into looper's loop.resolved.json shape, validated (368).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `loop_id (str).` |  |  |

## Returns

``{resolved, valid, findings}``.

## Chain-next

loop.emit(loop_id, target) to render the files.

## Details

(no further detail)

## Example

```bash
agency-loop-compile --intent-id $IID …
```
