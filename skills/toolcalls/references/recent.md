<!-- agency-generated: v1 -->
# toolcalls.recent

The most recent captured tool calls, in FULL (read-only).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `limit (int — max rows from the tail; default 20).` |  |  |

## Returns

``{calls: [{id, ts, phase, tool, input_json, output_json, filtered}], total}``.

## Chain-next

``toolcalls.top`` for the aggregate ranking.

## Details

(no further detail)

## Example

```bash
agency-toolcalls-recent --intent-id $IID …
```
