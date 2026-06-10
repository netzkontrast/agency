<!-- agency-generated: v1 -->
# novel.create_magic_system

Mint a MagicSystem under a World + PART_OF_WORLD edge (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `world_id, slug, name.` |  |  |

## Returns

``{magic_system_id, world_id, slug, name}``.

## Chain-next

``novel.create_world_axiom`` to encode its rules.

## Details

(no further detail)

## Example

```bash
agency-novel-create_magic_system --intent-id $IID …
```
