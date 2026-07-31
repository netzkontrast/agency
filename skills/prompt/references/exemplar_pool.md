<!-- agency-generated: v1 -->
# prompt.exemplar_pool

N example sentences from the alter's Sprach-DNA pool (transform), rotated deterministically by intent-id hash so successive drafts see varied exemplars — never the same three every call.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `alter_id, n (default 3).` |  |  |

## Returns

``{examples: [str], pool_size}``.

## Chain-next

``prompt.compose_voice_locked_brief`` embeds them.

## Details

(no further detail)

## Example

```bash
agency-prompt-exemplar_pool --intent-id $IID …
```
