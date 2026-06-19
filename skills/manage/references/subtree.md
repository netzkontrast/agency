<!-- agency-generated: v1 -->
# manage.subtree

SUBTREE — the ``PARENT_INTENT`` sub-intent tree rooted at an intent (root inclusive), walked over the typed ``parent_intent_id`` FK (Spec 330; makes ``IntentStore.intent_tree`` load-bearing).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `root_intent_id (str — the root Intent id).` |  |  |

## Returns

``{root_intent_id, count, intents: [props]}`` or ``{error}``.

## Chain-next

manage.provenance(intent_id) for one intent's full cross-concern provenance.

## Details

(no further detail)

## Example

```bash
agency-manage-subtree --intent-id $IID …
```
