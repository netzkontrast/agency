<!-- agency-generated: v1 -->
# develop.estimate

Decidable effort estimate from change-size inputs (Spec 046 F-D — sc-estimate, DECIDABLE only: no LLM, a transparent formula over the inputs you can count).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `loc (lines of change), files (files touched), tests (tests to write).` |  |  |

## Returns

``{points, bucket, confidence, drivers}`` — bucket ∈ S/M/L/XL; confidence falls as size grows (more unknowns).

## Chain-next

walk ``plan`` (large) or ``tdd`` (small) accordingly.

## Details

(no further detail)

## Example

```bash
agency-develop-estimate --intent-id $IID …
```
