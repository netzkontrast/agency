<!-- agency-generated: v1 -->
# music.measure_gate

Computed measure gate — composes loudness probe + range check (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, path, min_lufs, max_lufs.` |  |  |

## Returns

``{gate, passed, measured_lufs}`` or typed GATE_FAILED.

## Chain-next

on failure, ``music.master_audio`` to adjust.

## Details

Passes iff measured loudness ∈ [min_lufs, max_lufs] (i.e. within the sensible streaming-target window).

## Example

```bash
agency-music-measure_gate --intent-id $IID …
```
