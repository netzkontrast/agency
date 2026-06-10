<!-- agency-generated: v1 -->
# novel.check_crucial_element_placement

Decidable check (row 6): storyform.crucial_element_id == mc.problem_id.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `ncp (NCP v1.3.0 payload).` |  |  |

## Returns

``{passed, violations}``.

## Chain-next

``novel.check_resolve_outcome_judgment`` (row 7).

## Details

The crucial element is the storyform-level pivot point — by Dramatica convention it sits on mc.problem. Mismatch means the storyform's center of gravity moved without the throughline following it.

## Example

```bash
agency-novel-check_crucial_element_placement --intent-id $IID …
```
