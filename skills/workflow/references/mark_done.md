<!-- agency-generated: v1 -->
# workflow.mark_done

MARK_DONE — phase 14, the owner's done-cascade.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `spec_id, approver (owner identity — agent is rejected), apply (do the file writes), override (owner bypass of a skeleton-decision gate).` |  |  |

## Returns

``{spec_id, done, approved, themes_written, architecture_rebuilt, decisions}`` or, when the done move is illegal, ``{done: False, error}``.

## Chain-next

workflow.board to see the spec in /done.

## Details

(no further detail)

## Example

```bash
agency-workflow-mark_done --intent-id $IID …
```
