<!-- agency-generated: v1 -->
# dogfood.replay_events

Replay every Event recorded OBSERVED_DURING the given intent (Spec 195 Slice 2 — typed replay + monotonic chain).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `for_intent_id (str — required; the SERVES anchor). tool (str — optional filter; "" = every tool). limit (int — bound the row count; default 100).` |  |  |

## Returns

``{intent_id, events: [{event_id, prior_event_id, name, tool, session, target, verb_shadow, summary}], count}``.

## Chain-next

``dogfood.parse_amendment`` reads the replay when the classifier needs the recent-event window.

## Details

Returns the sequence of typed event rows in record order, each linked to its `prior_event_id` (the previous event in the same intent's replay; empty for the first). Slice 1 BoundaryUse nodes are joined in via the RECORDED_BY edge so the replay surface carries the moat metadata when present.

## Example

```bash
agency-dogfood-replay_events --intent-id $IID …
```
