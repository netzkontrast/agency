<!-- agency-generated: v1 -->
# novel.storyform_critical_pass

Critical-thinking pass over the storyform (act, xcap to thinking).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{result, artefact}`` thinking-analysis.

## Chain-next

revise storyform per the surfaced concerns.

## Details

Walks ``intent.apply_full_review`` against the novel's storyform body (or premise / title as fallback) and surfaces the 8-method scaffold as a thinking-analysis artefact. The xcap call records a SERVES edge from the thinking cap's Invocation back to this intent — provenance traversal sees the critique.

## Example

```bash
agency-novel-storyform_critical_pass --intent-id $IID …
```
