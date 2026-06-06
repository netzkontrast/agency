<!-- agency-generated: v1 -->
# delegate.join

Reduce a delegation over its children's Lifecycle state.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `delegation (Delegation node id from ``fan_out``).` |  |  |

## Returns

``{children, states, done, reduction}`` (wire shape); ``done=True`` iff every child Lifecycle is ``completed``; ``{error, delegation}`` on cross-intent rejection.

## Chain-next

when ``done=False``, walk the child lifecycles and address ``input-required`` pauses; re-call ``join``.

## Details

Writes a REDUCES_INTO reduction (so it is an ``act``, not a pure read).

## Example

```bash
agency-delegate-join --intent-id $IID …
```
