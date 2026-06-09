<!-- agency-generated: v1 -->
# music.qc_gate

Computed QC gate — composes 7-point QC checklist (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, path.` |  |  |

## Returns

``{gate, passed, summary, rows}`` or typed GATE_FAILED.

## Chain-next

on failure, fix the failing rows + re-check.

## Details

Passes iff zero ``fail`` rows in the 7-point checklist. ``warn`` rows are PASS-with-evidence (gate records the warn count).

## Example

```bash
agency-music-qc_gate --intent-id $IID …
```
