<!-- agency-generated: v1 -->
# novel.check_dynamic_pair_reciprocity

Decidable check (row 1): mc.dynamic and os.dynamic must differ.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `ncp (NCP v1.3.0 payload).` |  |  |

## Returns

``{passed, violations}``.

## Chain-next

``novel.check_throughline_partition`` (row 5).

## Details

In Dramatica, the mc/os throughline pair shares a binary dynamic axis (`thought` ↔ `knowledge`) — the same value on both sides collapses the pair. Same for ic/rs.

## Example

```bash
agency-novel-check_dynamic_pair_reciprocity --intent-id $IID …
```
