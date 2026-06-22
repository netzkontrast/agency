<!-- agency-generated: v1 -->
# loop.preview

Render the graph-derived ASCII flow preview of a loop (367 phase 6).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `loop_id (str).` |  |  |

## Returns

``{ascii, states, criteria, council, control}``.

## Chain-next

loop.emit(loop_id, target) to write the workspace.

## Details

(no further detail)

## Example

```bash
agency-loop-preview --intent-id $IID …
```
