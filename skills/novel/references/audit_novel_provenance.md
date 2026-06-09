<!-- agency-generated: v1 -->
# novel.audit_novel_provenance

Aggregate the provenance graph census for the serving intent (transform, xcap to analyze).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id (validated for NOT_FOUND only).` |  |  |

## Returns

``{novel_id, census, capabilities}``.

## Chain-next

revise the storyform per surfaced gaps.

## Details

Routes through ``analyze.graph`` to surface a node-type census + verb summary. The audit catches which cluster caps have SERVED the novel's intent across the session.

## Example

```bash
agency-novel-audit_novel_provenance --intent-id $IID …
```
