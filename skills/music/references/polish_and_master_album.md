<!-- agency-generated: v1 -->
# music.polish_and_master_album

Combined polish + master pipeline (effect); produces mastering-report.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, paths, target_lufs.` |  |  |

## Returns

``{result, artefact}`` with per-track gain summary.

## Chain-next

``music.qc_audio`` per output.

## Details

(no further detail)

## Example

```bash
agency-music-polish_and_master_album --intent-id $IID …
```
