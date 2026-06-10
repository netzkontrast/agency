<!-- agency-generated: v1 -->
# novel.flag_anachronistic_reference

Check if the character knows the fact yet (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id (the scene that references the fact), character_id, fact_text (the fact body to match).` |  |  |

## Returns

``{anachronism, expected_learned_in?, no_record?}``.

## Chain-next

revise the scene OR add a `record_character_learns` earlier in the manuscript.

## Details

Walks the character's KNOWS to find a matching fact; if found, compares LEARNED_IN scene's chapter number to the target scene's. When LEARNED_IN's chapter > target's chapter → anachronism (the character references something they haven't learned yet).

## Example

```bash
agency-novel-flag_anachronistic_reference --intent-id $IID …
```
