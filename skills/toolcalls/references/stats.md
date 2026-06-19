<!-- agency-generated: v1 -->
# toolcalls.stats

Capture counts broken down by phase and tool (read-only).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `(none).` |  |  |

## Returns

``{total, by_phase: {pre, post}, by_tool: {Bash, Read, …}}``.

## Chain-next

``toolcalls.top`` for the ranked shapes.

## Details

(no further detail)

## Example

```bash
agency-toolcalls-stats --intent-id $IID …
```
