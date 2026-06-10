<!-- agency-generated: v1 -->
# novel.list_world

Render a tree of a World's contents (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `world_id.` |  |  |

## Returns

``{world, cultures, religions, languages, magic_systems, axioms}``.

## Chain-next

``novel.find_axiom_contradictions`` for the rule audit.

## Details

Walks PART_OF_WORLD edges (Spec 125 `ctx.neighbors`) and groups the children by label.

## Example

```bash
agency-novel-list_world --intent-id $IID …
```
