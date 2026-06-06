<!-- agency-generated: v1 -->
# develop.checklist

Project a discipline (skill walk) into a step-by-step checklist.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `discipline (str — registered skill name).` |  |  |

## Returns

``{result: [{step, gate}, …]}`` ordered by phase index.

## Chain-next

walk the steps via the relevant capability verbs.

## Details

(no further detail)

## Example

```bash
agency-develop-checklist --intent-id $IID …
```
