<!-- agency-generated: v1 -->
# loop.emit

Project the loop to its portable workspace (loop.yaml/resolved/LOOP.md…) (368).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `loop_id (str), target (str — output directory).` |  |  |

## Returns

``{files, valid, findings}``.

## Chain-next

loop.emit_runner(loop_id, target) for the external runner.

## Details

(no further detail)

## Example

```bash
agency-loop-emit --intent-id $IID …
```
