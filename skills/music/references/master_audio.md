<!-- agency-generated: v1 -->
# music.master_audio

Master a single track via AudioDriver, producing a mastering-report (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, path, target_lufs, preset.` |  |  |

## Returns

``{result, artefact}`` with input/output paths + gain.

## Chain-next

``music.qc_audio`` to verify.

## Details

(no further detail)

## Example

```bash
agency-music-master_audio --intent-id $IID …
```
