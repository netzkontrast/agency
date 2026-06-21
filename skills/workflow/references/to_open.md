<!-- agency-generated: v1 -->
# workflow.to_open

TO_OPEN — phase 10: move the spec ``draft→open`` and extract its decisions into ``proposed`` drafts (`adr.extract_decisions apply=True`).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `spec_id (the spec Document id).` |  |  |

## Returns

``{spec_id, state, drafted: [decision_ids], candidates}``.

## Chain-next

workflow.approve_decisions then workflow.begin_impl.

## Details

(no further detail)

## Example

```bash
agency-workflow-to_open --intent-id $IID …
```
