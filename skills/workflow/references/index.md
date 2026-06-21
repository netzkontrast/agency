<!-- agency-generated: v1 -->
# workflow.index

INDEX — the "alle Specs sind indiziert, korrekte Frontmatter" guarantee (Spec 357).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `root (str — the Plan dir to index; default "Plan").` |  |  |

## Returns

``{root, count, rows: [{spec, spec_id, folder_state, frontmatter_state, node_state, flags}], drift, ok}`` — ``ok`` is True iff no spec carries a drift flag (the check-drift predicate).

## Chain-next

workflow.move_spec to reconcile a drifted spec; the check-drift spec-state gate consumes ``ok`` (follow-up).

## Details

(no further detail)

## Example

```bash
agency-workflow-index --intent-id $IID …
```
