<!-- agency-generated: v1 -->
# workflow.board

BOARD — the graph-native spec board: live SpecLifecycles grouped by their ``spec``-machine state (optionally filtered to one ``state``).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `state (str — optional filter to one spec state).` |  |  |

## Returns

``{board: {state: [{lifecycle_id, spec_id}]}, states, total}``.

## Chain-next

workflow.move_spec to advance one; adr.hints at inprogress.

## Details

(no further detail)

## Example

```bash
agency-workflow-board --intent-id $IID …
```
