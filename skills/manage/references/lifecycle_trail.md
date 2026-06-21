<!-- agency-generated: v1 -->
# manage.lifecycle_trail

LIFECYCLE WATCH — the Spec 341 `watch` frame: the ordered Spec 344 `lifecycle_transition` Event trail recorded `OBSERVED_DURING` this lifecycle (what `move` emits), so an observer reads the durable history instead of polling `state`.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id (str), limit (int — max events).` |  |  |

## Returns

``{lifecycle_id, count, transitions: [{from_state, to_state, evidence, at}]}`` or ``{error}`` if absent / not a Lifecycle.

## Chain-next

manage.lifecycle(lifecycle_id) for the current rolled-up state.

## Details

(no further detail)

## Example

```bash
agency-manage-lifecycle_trail --intent-id $IID …
```
