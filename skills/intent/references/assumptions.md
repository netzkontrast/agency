<!-- agency-generated: v1 -->
# intent.assumptions

Surface + classify the implicit assumptions a goal rests on (load-bearing vs not).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `subject (defaults to the serving intent).` |  |  |

## Returns

a scaffold separating assumptions you can test cheaply now.

## Chain-next

``intent.premortem`` on the load-bearing ones.

## Details

(no further detail)

## Example

```bash
agency-intent-assumptions --intent-id $IID …
```
