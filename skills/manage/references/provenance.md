<!-- agency-generated: v1 -->
# manage.provenance

PROVENANCE — the typed cross-concern join (Spec 330/290, Memory · Capability · Lifecycle): every Invocation serving the intent + its Agent + the Artefacts it produced (or that serve the intent) + the Lifecycle states, read through the typed ``IntentStore`` join rather than a Cypher traversal.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `for_intent_id (str — the Intent id).` |  |  |

## Returns

``{intent_id, invocations, agents, artefacts, lifecycle, counts}`` or ``{error}`` if not an Intent.

## Chain-next

manage.timeline(intent_id) for the time order; manage.subtree(intent_id) for its sub-intents.

## Details

(no further detail)

## Example

```bash
agency-manage-provenance --intent-id $IID …
```
