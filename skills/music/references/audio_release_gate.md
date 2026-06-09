<!-- agency-generated: v1 -->
# music.audio_release_gate

Composite audio-release gate — every track QC-passed (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, album.` |  |  |

## Returns

``{gate, passed, mastered_count, qc_failures}`` or GATE_FAILED.

## Chain-next

master the unmastered + fix QC fails.

## Details

Passes iff every track in the album has status=mastered (per the StateDriver) AND no track's QC checklist returns a `fail`.

## Example

```bash
agency-music-audio_release_gate --intent-id $IID …
```
