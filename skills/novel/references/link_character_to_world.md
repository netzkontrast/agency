<!-- agency-generated: v1 -->
# novel.link_character_to_world

Add a typed edge from Character → World child (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `character_id, target_id, edge_kind.` |  |  |

## Returns

``{character_id, target_id, edge_kind}``.

## Chain-next

continue weaving the character into the world.

## Details

``edge_kind`` is constrained to the documented set: ``BELONGS_TO`` (catch-all), ``INHABITS`` (lives in / Culture), ``WORSHIPS`` (Religion), ``SPEAKS`` (Language), ``WIELDS`` (MagicSystem). The orchestrator picks one matching the target's label.

## Example

```bash
agency-novel-link_character_to_world --intent-id $IID …
```
