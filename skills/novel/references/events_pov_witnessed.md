<!-- agency-generated: v1 -->
# novel.events_pov_witnessed

The POV knowledge intersection (transform): events REVEALED_IN a scene the character fronts (``pov_character_id``), optionally cut to those with ``when_story`` < ``before_when``. |witnessed| ≤ |all|.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `character_id, before_when (optional when_story ceiling).` |  |  |

## Returns

``{events: [{event_id, label, when_story}], total_events}``.

## Chain-next

compare against Spec 131's KnownFact ledger.

## Details

(no further detail)

## Example

```bash
agency-novel-events_pov_witnessed --intent-id $IID …
```
