<!-- agency-generated: v1 -->
# document.explain

Deterministic code → markdown explanation; emits a Reflection.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `target (str — file path | module | module.symbol), depth (str — brief | standard | deep).` |  |  |

## Returns

``{reflection_id, content, tokens}``.

## Chain-next

caller renders or stores the content.

## Details

(no further detail)

## Example

```bash
agency-document-explain --intent-id $IID …
```
