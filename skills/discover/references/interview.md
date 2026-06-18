<!-- agency-generated: v1 -->
# discover.interview

Run the adaptive elicitation interview → a DRAFT Intent (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `seed` | the one-sentence ask the interview sharpens) - answers (the verbatim user answers the harness folds back, in order; empty → an empty-but-recorded run) - max_beats (the budget; termination is data-driven, not this count |  |

## Returns

``{session_id, intent_id, beats:[{turn_id,beat,kind,question, answer}], terminated_by:"complete"|"max_beats", clarity_inputs}``.

## Chain-next

``discover.clarity`` (Spec 322) scores + the confirm gate flips the draft Intent to confirmed.

## Details

Opens a ``DiscoverySession``, runs up to ``max_beats`` beats (each beat's question derived from the prior answer — the adaptivity seam), records an ``ElicitationTurn`` per beat (``ELICITS`` edge), then mints a *draft* Intent (never confirmed — the clarity gate Spec 322 owns that) with a ``DISCOVERED`` edge from the session.

## Example

```bash
agency-discover-interview --intent-id $IID …
```
