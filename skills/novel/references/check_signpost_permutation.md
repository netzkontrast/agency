<!-- agency-generated: v1 -->
# novel.check_signpost_permutation

Decidable check (row 10): signposts in canonical order per class.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `ncp (NCP v1.3.0 payload).` |  |  |

## Returns

``{passed, violations}``.

## Chain-next

gated behind row 5 in the composite.

## Details

Each class has a canonical ordering of its 4 types (the Dramatica signpost sequence). A reordering signals an authoring drift.

## Example

```bash
agency-novel-check_signpost_permutation --intent-id $IID …
```
