<!-- agency-generated: v1 -->
# music.master_album

Master an audio file to a target loudness via the AudioDriver (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, path, target_lufs.` |  |  |

## Returns

``{result, artefact}`` where artefact.kind = ``mastering-report`` with measured_lufs, target_lufs, gain_db.

## Chain-next

``music.publish_asset``.

## Details

Reads measured loudness, applies the gain via ffmpeg (both through the driver — no direct ffmpeg/pyloudnorm), and records a ``mastering-report``.

## Example

```bash
agency-music-master_album --intent-id $IID …
```
