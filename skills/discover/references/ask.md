<!-- agency-generated: v1 -->
# discover.ask

Build ONE well-formed AskUserQuestion payload from DERIVED options (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `context` | list of ``{id, text}`` items — the derivation sources; >= 2) - question (the question text; derived from context when omitted) - n_options (clamped to [2, 4]); multi (multiSelect — independent axes only); ambiguity_kind (Spec 307 enum); header (<= 12 chars; derived when omitted |  |

## Returns

``{payload: {question, header, options[], multiSelect}, question_id}``.

## Chain-next

render ``payload`` via AskUserQuestion, then fold the answer (``discover.clarify`` / ``interview`` / ``scope`` write the caller-appropriate edge).

## Details

Every option is DERIVED from a supplied context item and carries that item's id as ``provenance``; an invented option (no resolvable provenance) is rejected, never shown to the user. Records a *pending* ``ClarificationQuestion``; the caller folds the answer back (no Intent mutation here — Spec 307 rule 3).

## Example

```bash
agency-discover-ask --intent-id $IID …
```
