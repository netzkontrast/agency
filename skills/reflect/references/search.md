<!-- agency-generated: v1 -->
# reflect.search

Keyword search over reflection text (deterministic substring match).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `query (str — case-insensitive substring).` |  |  |

## Returns

``{result: [{scope, text}, …]}``.

## Chain-next

``reflect.recall_semantic`` for semantic ranking when a stronger backend is wired.

## Details

(no further detail)

## Example

```bash
agency-reflect-search --intent-id $IID …
```
