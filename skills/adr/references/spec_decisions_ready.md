<!-- agency-generated: v1 -->
# adr.spec_decisions_ready

SPEC_DECISIONS_READY — the /open→/inprogress predicate (358).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `spec_id (a Document id OR a frontmatter spec_id).` |  |  |

## Returns

``{spec_id, ready, decisions: [{id, status}], blocking: [ids], reason?}``.

## Chain-next

workflow.move_spec(spec, "inprogress") guards on ``ready``.

## Details

(no further detail)

## Example

```bash
agency-adr-spec_decisions_ready --intent-id $IID …
```
