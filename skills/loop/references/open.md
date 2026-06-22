<!-- agency-generated: v1 -->
# loop.open

Open a loop Lifecycle SERVING the goal Intent; refuses a guard-free loop (366).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `goal_id (str — the goal Intent), max_iterations (int), max_revisions (int), budget (dict|None), no_progress_stall (int).` |  |  |

## Returns

``{loop_id, state, control}``.

## Chain-next

loop.advance(loop_id) to walk it.

## Details

(no further detail)

## Example

```bash
agency-loop-open --intent-id $IID …
```
