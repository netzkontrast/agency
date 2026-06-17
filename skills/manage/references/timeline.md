<!-- agency-generated: v1 -->
# manage.timeline

TIMELINE — the ordered Event + Invocation history for an intent (Spec 290, Lifecycle · Memory).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `for_intent_id (str — the Intent id), limit (int — max events).` |  |  |

## Returns

``{intent_id, count, timeline: [{kind, name, at}]}`` ordered by valid-time.

## Chain-next

manage.artefacts(intent_id) for what it produced.

## Details

(no further detail)

## Example

```bash
agency-manage-timeline --intent-id $IID …
```
