<!-- agency-generated: v1 -->
# jules.patch_body

Explicit, capped unidiff retrieval for one of the session's outputs.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session (sid), output_index (int, default 0), max_bytes (int — default 4096; capped slice).` |  |  |

## Returns

``{unidiff, truncated, original_bytes}`` or ``{error}`` on out-of-range index.

## Chain-next

``jules.apply_patch(session=)`` for the recovery plan.

## Details

Default cap 4 KB so a careless call can't blow the agent's context.

## Example

```bash
agency-jules-patch_body --intent-id $IID …
```
