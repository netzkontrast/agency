<!-- agency-generated: v1 -->
# adr.update

UPDATE a ``Decision`` in place — advance its ``status`` and/or fill WH(Y) elements + governance incrementally (the DOMAIN mutator; never reach into `manage` for an ADR).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `decision_id (str), status (the decision_status enum — transition must be legal), any WH(Y) element, next_review (ISO date — the cadence `review_sweep` reads), review_cadence (str). Empty = unchanged.` |  |  |

## Returns

``{id, updated: [field…]}`` or ``{error, rule}``.

## Chain-next

adr.validate(id); adr.review_sweep() for the cadence sweep.

## Details

(no further detail)

## Example

```bash
agency-adr-update --intent-id $IID …
```
