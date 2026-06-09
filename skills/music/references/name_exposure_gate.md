<!-- agency-generated: v1 -->
# music.name_exposure_gate

Computed name-exposure gate — no forbidden roster names in lyrics (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, lyrics, roster (defaults to config blocklist).` |  |  |

## Returns

``{gate, passed, hits}`` or typed GATE_FAILED.

## Chain-next

on failure, replace the leaked name with a function/role descriptor then re-check.

## Details

Spec 119 — F6 from Spec 117. Passes iff zero rostered personal/character names appear (whole-word, case-insensitive). When `roster` is None it defaults to the project's ``name_exposure.blocklist``; an empty roster yields zero hits → PASSED (no-op for rosterless projects). Records PASSED/BLOCKED_ON on the lifecycle via gate.check.

## Example

```bash
agency-music-name_exposure_gate --intent-id $IID …
```
