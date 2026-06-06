<!-- agency-generated: v1 -->
# analyze.run

Run the requested axes; record an Analysis + per-Finding nodes.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `path (str), axes (list[str] — default` |  | all four), lang (str — only 'py' in v1). |

## Returns

``{analysis_id, totals: {axis: {info, warn, fail}}}`` — compact summary; detail lives in the graph as Analysis → HAS_FINDING → Finding nodes.

## Chain-next

``analyze.improve(analysis_id)`` or ``analyze.cleanup(path)``.

## Details

(no further detail)

## Example

```bash
agency-analyze-run --intent-id $IID …
```
