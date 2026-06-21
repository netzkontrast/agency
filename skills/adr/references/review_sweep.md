<!-- agency-generated: v1 -->
# adr.review_sweep

REVIEW_SWEEP — cadence governance (Spec 355 S2, SPEC-001-A): flip every live ``approved``/``implemented`` decision whose ``next_review`` date has lapsed (< today) to ``expired`` — a legal `decision`-machine transition.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `today (ISO 'YYYY-MM-DD'; default = the system date).` |  |  |

## Returns

``{swept: [decision_ids], count, as_of}``.

## Chain-next

adr.catalogue(status="expired") to review what lapsed.

## Details

(no further detail)

## Example

```bash
agency-adr-review_sweep --intent-id $IID …
```
