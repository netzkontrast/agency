<!-- agency-generated: v1 -->
# novel.check_throughline_partition

Decidable check (row 5): 4 throughlines / 4 distinct Classes (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `ncp (the NCP v1.3.0 storyform payload — top-level dict with ``storyform.throughlines.{mc,os,ic,rs}.class_id``).` |  |  |

## Returns

``{passed, violations}`` — violations is a list of short codes (≤120 chars each per the report-shape budget in Spec 103 §"Done When").

## Chain-next

``novel.check_quad_completeness`` then the composite ``novel_coherence_check`` (Slice 2).

## Details

(no further detail)

## Example

```bash
agency-novel-check_throughline_partition --intent-id $IID …
```
