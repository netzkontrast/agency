<!-- agency-generated: v1 -->
# novel.record_storyform_decision

Record a contested storyform decision (effect, xcap to dogfood).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, decision, rationale (optional).` |  |  |

## Returns

``{novel_id, decision_id, decision}``.

## Chain-next

continue authoring; later ``analyze.graph`` reads the audit trail.

## Details

Routes through ``dogfood.record_decision`` so the decision lands in the cluster-wide decision audit. ``subject`` is bound to the novel id so analyses can filter by story.

## Example

```bash
agency-novel-record_storyform_decision --intent-id $IID …
```
