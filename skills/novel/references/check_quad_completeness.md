<!-- agency-generated: v1 -->
# novel.check_quad_completeness

Decidable check (row 3): mc problem and solution are paired.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `ncp (NCP v1.3.0 payload).` |  |  |

## Returns

``{passed, violations}``.

## Chain-next

gated behind row 5 in the composite (per Slice-2 lesson).

## Details

Resolves each via ``_resolve_term`` (kind-agnostic; tolerates ``el.*`` vs ``var.*``), then asserts the resolved problem's ``dynamic_pair_id`` slug matches the resolved solution's slug.

## Example

```bash
agency-novel-check_quad_completeness --intent-id $IID …
```
