<!-- agency-generated: v1 -->
# analyze.record_run

Record a QualityRun history node + return the trend (Spec 381 §3).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `mode, scope (str), findings (wire dicts), preset ('' → config strictness), status (complete|incomplete), config (quality` |  | block). |

## Returns

{run_id, mode, score, counts, status, trend:{first, prior, delta}}.

## Chain-next

manage.timeline(intent_id) / analyze.graph('QualityRun') for the series.

## Details

History is a GRAPH QUERY, never a ``.brooks-lint-history.json`` sidecar (Goal 2; survives ephemeral containers). Computes the Health Score + tier counts from the findings (honouring the quality: config), records a ``QualityRun{mode, scope, score, critical, warning, suggestion, status, recorded_at}`` SERVING the intent, then derives the trend: the delta from the most recent prior **complete** same-mode run. An incomplete/crashed walk is recorded but EXCLUDED from the delta (Nygard); a first run reports ``first=True``. Use when: persisting a review run so its score trend survives across sessions/CI as a durable, queryable node.

## Example

```bash
agency-analyze-record_run --intent-id $IID …
```
