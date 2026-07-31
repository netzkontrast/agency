<!-- agency-generated: v1 -->
# novel.get_voice_profile

Read the character's voice profile (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `character_id.` |  |  |

## Returns

the profile dict (all fields) or NOT_FOUND.

## Chain-next

``novel.score_voice_match(character_id, body)``.

## Details

(no further detail)

## Example

```bash
agency-novel-get_voice_profile --intent-id $IID …
```
