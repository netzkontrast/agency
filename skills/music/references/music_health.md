<!-- agency-generated: v1 -->
# music.music_health

Self-check the music capability (transform, driver-free) — report which Driver seams are wired.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `none.` |  |  |

## Returns

``{ok, drivers_wired, drivers_missing}``.

## Chain-next

register any missing driver via ``Engine(..., drivers=…)``.

## Details

Produces a deterministic readiness report listing wired vs. missing driver seams.

## Example

```bash
agency-music-music_health --intent-id $IID …
```
