<!-- agency-generated: v1 -->
# music.reset_mastering

Revert all master/polish state for an album (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album (slug).` |  |  |

## Returns

``{album, reset, tracks_reset}``.

## Chain-next

re-run ``music.polish_and_master_album``.

## Details

Delegates to ``music.set_track_status`` per track so each flip records its own Invocation in provenance (review finding: direct StateDriver writes lose the per-track audit trail). The sibling verb also enforces the ``TRACK_STATUS`` enum at write time.

## Example

```bash
agency-music-reset_mastering --intent-id $IID …
```
