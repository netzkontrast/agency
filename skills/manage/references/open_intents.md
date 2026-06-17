<!-- agency-generated: v1 -->
# manage.open_intents

OPEN-INTENTS — live intents + acceptance + SERVES subtree size, busiest first (Spec 290, Intent pillar).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `top (int — how many busiest intents to return).` |  |  |

## Returns

``{count, intents: [{id, purpose, acceptance, status, serves_count}]}``.

## Chain-next

manage.timeline(intent_id) for an intent's event order.

## Details

(no further detail)

## Example

```bash
agency-manage-open_intents --intent-id $IID …
```
