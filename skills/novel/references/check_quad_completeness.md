<!-- agency-generated: v1 -->
# novel.check_quad_completeness

Decidable check (row 3): quad-reverse-index audit.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `ncp (NCP v1.3.0 payload).` |  |  |

## Returns

``{passed, violations}``.

## Chain-next

``novel.check_throughline_partition``.

## Details

Verifies the crucial_element_id resolves and the MC's problem + solution elements (Spec 103 §"Decidable" row 3) are declared and sit on a known dynamic pair within the Dramatica ontology.

## Example

```bash
agency-novel-check_quad_completeness --intent-id $IID …
```
