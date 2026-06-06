<!-- agency-generated: v1 -->
# shell.filter

Filter text to a token-bounded slice — pure, no execution (hook-ready).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `text (raw output), spec (full|tail` |  | N|head:N|grep:PAT|lines:A-B|count|last). |

## Returns

``{result: {output, lines, spec}}``.

## Chain-next

forward the trimmed output (e.g. from a PostToolUse hook).

## Details

(no further detail)

## Example

```bash
agency-shell-filter --intent-id $IID …
```
