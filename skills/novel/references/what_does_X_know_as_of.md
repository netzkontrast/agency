<!-- agency-generated: v1 -->
# novel.what_does_X_know_as_of

List facts the character has learned ≤ the scene's narrative position (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `character_id, scene_id.` |  |  |

## Returns

``{facts: [{fact_id, fact, learned_in_scene}]}``.

## Chain-next

feed into ``prompt.assemble_scene_brief``'s pov_card.

## Details

Narrative-position is approximated by the chapter number of the LEARNED_IN scene vs the target scene. When chapter numbers tie, scene-creation order within the chapter is the tie-breaker.

## Example

```bash
agency-novel-what_does_X_know_as_of --intent-id $IID …
```
