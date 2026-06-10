<!-- agency-generated: v1 -->
# novel.check_approach_concern

Mostly-decidable check (row 8): approach ↔ class compatibility (WARN-severity).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `ncp (NCP v1.3.0 payload).` |  |  |

## Returns

``{passed: True, violations: [], warnings: [str]}``.

## Chain-next

``novel.check_mental_sex_problem_solving`` (row 9).

## Details

Per Dramatica theory: Do-er approach pairs with Universe/Physics classes; Be-er pairs with Mind/Psychology. Mismatch is a soft signal — emits ``warnings``, not ``violations``, so the composite passes-with-note instead of blocking.

## Example

```bash
agency-novel-check_approach_concern --intent-id $IID …
```
