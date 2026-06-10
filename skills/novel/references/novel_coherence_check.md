<!-- agency-generated: v1 -->
# novel.novel_coherence_check

Composite gate (Spec 120): runs all 11 storyform checks with chaining.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `ncp (NCP v1.3.0 payload).` |  |  |

## Returns

``{passed, violations: [{check, message}], warnings: [{check, message}]}``.

## Chain-next

terminal — orchestrator gates on ``passed``.

## Details

Chain order (Rec 2 exact-fail contract): row 5 (throughline_partition) → if pass → rows 3 (quad_completeness) + 10 (signpost_permutation) if row 10 pass → row 2 (ktad_coverage) rows 1, 4, 6, 7, 8 (WARN), 9, 11 always run. Records a ``gate.check(name="storyform-coherent")`` Gate node and a ``dogfood.record_decision`` for traceability.

## Example

```bash
agency-novel-novel_coherence_check --intent-id $IID …
```
