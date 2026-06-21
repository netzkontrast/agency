<!-- agency-generated: v1 -->
# workflow.move_spec

MOVE_SPEC — advance the spec's Lifecycle to ``to_state`` via ``ctx.lifecycle.move`` (the SOLE state writer — Spec 339; an illegal edge is rejected by the ``spec`` machine's transition table).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `spec_id (the spec Document id), to_state (a ``spec`` machine state), override (bool — owner bypass of the ADR gate).` |  |  |

## Returns

``{spec_id, lifecycle_id, moved, state, …}``; on the gate, ``{moved: False, blocked: True, reason, blocking}``; on an illegal edge / no-op, ``{moved: False, error}``.

## Chain-next

workflow.board to see the spec's new column.

## Details

(no further detail)

## Example

```bash
agency-workflow-move_spec --intent-id $IID …
```
