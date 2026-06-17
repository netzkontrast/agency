<!-- agency-generated: v1 -->
# research.lead

Scope a research question and plan specialists, minting a Research node.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `question (str), depth (str — brief|standard|deep).` |  |  |

## Returns

``{research_id, specialists, plan}``.

## Chain-next

``research.specialist`` per planned role.

## Details

(no further detail)

## Example

```bash
agency-research-lead --intent-id $IID …
```
