<!-- agency-generated: v1 -->
# novel.update_voice_profile

Partial update of any profile field (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `character_id + any of vocabulary_floor / sentence_avg_target / sentence_avg_stddev / taboo_words / signature_phrases / formality_target / contractions.` |  |  |

## Returns

``{profile_id, updated: [fields]}``.

## Chain-next

``novel.score_voice_match`` to re-measure.

## Details

(no further detail)

## Example

```bash
agency-novel-update_voice_profile --intent-id $IID …
```
