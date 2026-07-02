<!-- agency-generated: v1 -->
# prompt.compose_voice_locked_brief

Compose the §-structured voice-locked drafting brief for one scene and one fronting alter (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id, alter_id, allow_max_pair (explicit override), max_tokens (cap 3000; §EXAMPLES truncate first, then §SIGNATURE, never §TABOO).` |  |  |

## Returns

``{brief, artefact_id, sections}`` or ``{refused: True, reason, pair, advice}``.

## Chain-next

run the draft, then ``prompt.voice_drift_audit(scene_id)``.

## Details

(no further detail)

## Example

```bash
agency-prompt-compose_voice_locked_brief --intent-id $IID …
```
