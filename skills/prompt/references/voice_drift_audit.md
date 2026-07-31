<!-- agency-generated: v1 -->
# prompt.voice_drift_audit

Post-draft defensive audit (act): scan the drafted body against the assigned alter's profile — forbidden lexicon, taboo violations, signature presence, a register score — and flag ``leaked-other-alter`` when the body matches a DIFFERENT bound alter's voice better.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id.` |  |  |

## Returns

``{passed, forbidden_lexicon_hits, taboo_violations, signature_phrase_presence, register_match_score, verdict}``.

## Chain-next

redraft on ``drifted``/``leaked-other-alter``.

## Details

(no further detail)

## Example

```bash
agency-prompt-voice_drift_audit --intent-id $IID …
```
