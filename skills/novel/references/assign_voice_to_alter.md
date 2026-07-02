<!-- agency-generated: v1 -->
# novel.assign_voice_to_alter

Bind a Spec 134 ``VoiceProfile`` to an alter (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `alter_id, voice_profile_id.` |  |  |

## Returns

``{alter_id, voice_profile_id, replaced_voice}``.

## Chain-next

``novel.switching_log`` infers fronting from the bound voices.

## Details

(no further detail)

## Example

```bash
agency-novel-assign_voice_to_alter --intent-id $IID …
```
