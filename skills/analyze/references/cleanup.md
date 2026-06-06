<!-- agency-generated: v1 -->
# analyze.cleanup

Focused mode: analyse for dead-code findings only, draft a patch plan.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `path (str), dry_run (bool — v1` |  | dry-run only; apply is v2). |

## Returns

``{improvement_plan_id, item_count, summary}``.

## Chain-next

``gate.check`` before writes (v2).

## Details

(no further detail)

## Example

```bash
agency-analyze-cleanup --intent-id $IID …
```
