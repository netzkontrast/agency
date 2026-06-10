<!-- agency-generated: v1 -->
# novel.create_world

Mint a World node + SERVES intent (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `slug (URL-safe handle), name (human label).` |  |  |

## Returns

``{world_id, slug, name}``.

## Chain-next

``novel.create_culture`` / ``create_religion`` / ``create_language`` / ``create_magic_system`` / ``create_world_axiom`` to populate it.

## Details

(no further detail)

## Example

```bash
agency-novel-create_world --intent-id $IID …
```
