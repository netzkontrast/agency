<!-- agency-generated: v1 -->
# novel.check_ktad_coverage

Decidable check (row 2): concern_id == signposts[0] (K-position).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `ncp (NCP v1.3.0 payload).` |  |  |

## Returns

``{passed, violations}``.

## Chain-next

gated behind row 10 in the composite — only runs when signposts are in a canonical permutation.

## Details

The first signpost is the concern's KTAD-K anchor for that throughline. A mismatch means the concern wandered from its K slot.

## Example

```bash
agency-novel-check_ktad_coverage --intent-id $IID …
```
