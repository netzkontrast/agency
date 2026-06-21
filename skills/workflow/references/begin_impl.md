<!-- agency-generated: v1 -->
# workflow.begin_impl

BEGIN_IMPL — phase 12: the guarded ``open→inprogress`` move (BLOCKED by the ADR hinge until every decision is approved — `spec_decisions_ready`), then load the approved decisions' `adr.hints` into the build context.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `spec_id, budget (hint token budget).` |  |  |

## Returns

``{spec_id, begun, state, hints, hint_count}`` or, when the hinge blocks, ``{begun: False, blocked: True, reason, blocking}``.

## Chain-next

implement against the hints; workflow.move_spec(→done) when verified.

## Details

(no further detail)

## Example

```bash
agency-workflow-begin_impl --intent-id $IID …
```
