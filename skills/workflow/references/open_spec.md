<!-- agency-generated: v1 -->
# workflow.open_spec

OPEN_SPEC — mint a SpecLifecycle (machine ``spec``, state ``draft``) for a spec ``Document``, ``TRACKS``-bound to it and SERVING the intent.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `spec_id (the spec's Document id), title (str — optional label).` |  |  |

## Returns

``{spec_id, lifecycle_id, state, created}`` or ``{error}``.

## Chain-next

workflow.move_spec(spec_id, "open") once design is done.

## Details

(no further detail)

## Example

```bash
agency-workflow-open_spec --intent-id $IID …
```
