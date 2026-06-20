<!-- agency-generated: v1 -->
# frugal.instructions

Return the frugal ruleset text at a level — the ponytail-MCP port (``ponytail_instructions``).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `level (str — off|lite|full|ultra; empty = the active level).` |  |  |

## Returns

``{level, instructions}`` (instructions is empty at level off).

## Chain-next

inject the returned text as the session's discipline.

## Details

(no further detail)

## Example

```bash
agency-frugal-instructions --intent-id $IID …
```
