<!-- agency-generated: v1 -->
# manage.whats_next

WHATS-NEXT — blocked items + the next actions against an intent's acceptance (Spec 290, Lifecycle pillar; the navigate core).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `for_intent_id (str — the Intent id).` |  |  |

## Returns

``{intent_id, acceptance, status, done, blocked, next}``.

## Chain-next

manage.timeline(intent_id) for the full event order.

## Details

Reads the Lifecycles + Gates serving the intent: anything awaiting input/auth or failed (or an explicit ``BLOCKED_ON`` dependency) is ``blocked``; anything still submitted/working is in flight; with neither and the acceptance unmet, the acceptance itself is surfaced as the next action.

## Example

```bash
agency-manage-whats_next --intent-id $IID …
```
