<!-- agency-generated: v1 -->
# loop.register_model

Register a model invocation — argv-only, rejects secret-shaped material (369).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `cli (str), family (str), invoke (argv list), local (bool), store_path (str — optional config path).` |  |  |

## Returns

``{registered, ...}`` or ``{error}``.

## Chain-next

loop.add_member(loop_id, ...) referencing the family.

## Details

(no further detail)

## Example

```bash
agency-loop-register_model --intent-id $IID …
```
