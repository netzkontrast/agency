<!-- agency-generated: v1 -->
# manage.state

STATE rollup — the "where are we" dashboard (Spec 290, on manage).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `for_intent_id (str — optional; scopes the rollup to one intent).` |  |  |

## Returns

``{intents, reflections, artefacts, lifecycles_by_state, …}``.

## Chain-next

manage.open_intents / manage.timeline to drill in.

## Details

Cross-pillar current state: live counts of Intents / Reflections / Artefacts and Lifecycles grouped by state. With ``intent_id``, also the size of its ``SERVES`` subtree + artefacts produced under it.

## Example

```bash
agency-manage-state --intent-id $IID …
```
