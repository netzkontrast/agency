<!-- agency-generated: v1 -->
# develop.reference

Fetch a discipline's heavy how-to on demand (T3 disclosure).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `topic (one of testing-skills | skill-descriptions | best-practices | …).` |  |  |

## Returns

``{topic, doc}`` on hit; ``{error, available}`` on miss (both at the wire — engine strips the internal envelope).

## Chain-next

terminal — caller reads the doc.

## Details

(no further detail)

## Example

```bash
agency-develop-reference --intent-id $IID …
```
