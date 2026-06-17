<!-- agency-generated: v1 -->
# manage.render

RENDER the read-API as a compact markdown dashboard — the "where are we" view, rule-2 graph→markdown on demand (Spec 290 Slice 2).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `for_intent_id (str — optional; adds the intent's next/blocked section), top (int — open-intents rows to list).` |  |  |

## Returns

``{view, markdown}``.

## Chain-next

manage.timeline(intent_id) / manage.artefacts(intent_id).

## Details

Composes ``state`` + ``open_intents`` (and, when an intent is named, ``whats_next``) into one human-readable projection. Read-only: it calls the sibling read verbs, never writes.

## Example

```bash
agency-manage-render --intent-id $IID …
```
