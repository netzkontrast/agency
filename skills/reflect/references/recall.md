<!-- agency-generated: v1 -->
# reflect.recall

Retrieve reflections, newest first, optionally filtered by scope.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scope (str — optional filter; empty returns all).` |  |  |

## Returns

``{result: [{scope, text}, …]}`` newest-first.

## Chain-next

terminal — caller renders/aggregates the list.

## Details

(no further detail)

## Example

```bash
agency-reflect-recall --intent-id $IID …
```
