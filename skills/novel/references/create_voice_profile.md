<!-- agency-generated: v1 -->
# novel.create_voice_profile

Mint (or overwrite) the character's ``VoiceProfile`` + ``VOICE_OF`` edge (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `character_id, vocabulary_floor (min unique-word ratio), sentence_avg_target/-stddev, taboo_words (csv), signature_phrases (csv), formality_target (low|medium|high), contractions (bool).` |  |  |

## Returns

``{profile_id, character_id, derived_from_scenes}``.

## Chain-next

``novel.check_pov_voice(scene_id)`` per drafted scene.

## Details

Unset sentence targets are DERIVED from the character's already- drafted scenes when ≥ 5 carry bodies (rule 8 — computed defaults, not snapshots); below that the author authors them directly.

## Example

```bash
agency-novel-create_voice_profile --intent-id $IID …
```
