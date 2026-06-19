<!-- agency-generated: v1 -->
# toolcalls.top

The top captured tool-call shapes by frequency × payload cost (read-only).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `n (int — how many shapes; default 20).` |  |  |

## Returns

``{top: [{tool, shape, calls, bytes, sample}], total}``.

## Chain-next

``toolcalls.export`` to distil these into a durable report.

## Details

Identical (tool, input) calls are grouped — a command run 30× ranks above a one-off — so this surfaces the repeated/expensive work worth a capability or a filter.

## Example

```bash
agency-toolcalls-top --intent-id $IID …
```
