<!-- agency-generated: v1 -->
# novel.check_slot_fill

Decidable check (row 4): no null required slots (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `ncp (NCP v1.3.0 payload).` |  |  |

## Returns

``{passed, violations}``.

## Chain-next

``novel.check_throughline_partition`` for H1+H2.

## Details

Each throughline must carry non-null `class_id`, `concern_id`, `approach`, `mental_sex`, `resolve` slots (or omit the slot entirely — explicit null is a fill error, not absence).

## Example

```bash
agency-novel-check_slot_fill --intent-id $IID …
```
