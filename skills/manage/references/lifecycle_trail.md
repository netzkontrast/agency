<!-- agency-generated: v1 -->
# manage.lifecycle_trail

LIFECYCLE WATCH — the Spec 341 `watch` frame: the ordered Spec 344 `lifecycle_transition` Event trail recorded `OBSERVED_DURING` a lifecycle (what `move` emits), so an observer reads the durable history instead of polling `state`.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id (str) XOR scope (str), limit (int — max events).` |  |  |

## Returns

per-id ``{lifecycle_id, count, transitions:[{from_state, to_state, evidence, at}]}``; per-scope ``{scope, lifecycles, count, transitions:[{…, lifecycle_id}]}``; or ``{error}`` (absent / not-a-Lifecycle, or neither arg given).

## Chain-next

manage.lifecycle(lifecycle_id) for the current rolled-up state.

## Details

Two modes (Spec 341 Slice 2): - ``lifecycle_id`` → one lifecycle's trail (the original `watch` frame). - ``scope`` (no id) → the UNIFIED board trail: every durable transition across all live Lifecycles whose ``kind`` / ``machine`` / ``parameterization`` matches ``scope`` (e.g. ``scope="jules"`` folds the whole jules board's history into one view), each transition tagged with its ``lifecycle_id``. This is how the observe suite surfaces the in-flight board, not only a single id.

## Example

```bash
agency-manage-lifecycle_trail --intent-id $IID …
```
