<!-- agency-generated: v1 -->
# novel.check_mental_sex_problem_solving

Decidable check (row 9): mental_sex ↔ class compatibility.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `ncp (NCP v1.3.0 payload).` |  |  |

## Returns

``{passed, violations}``.

## Chain-next

``novel.check_signpost_permutation`` (row 10).

## Details

Parallel rule to row 8 but on the mental_sex axis. Universe / Physics classes pair with ``linear`` problem-solving (sequential, cause→effect); Mind / Psychology pair with ``holistic`` (gestalt, whole-system). Mismatch is a structural violation.

## Example

```bash
agency-novel-check_mental_sex_problem_solving --intent-id $IID …
```
