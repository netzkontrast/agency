<!-- agency-generated: v1 -->
# analyze.improve

Read prior Analysis findings, draft an improvement plan as a Reflection.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `analysis_id (str — from a prior ``analyze.run``), axes (list[str] — filter findings to these axes), apply (bool — v1` |  | planning only; apply path is v2). |

## Returns

``{improvement_plan_id, item_count, summary}``.

## Chain-next

``gate.check`` per cluster before applying (v2).

## Details

(no further detail)

## Example

```bash
agency-analyze-improve --intent-id $IID …
```
