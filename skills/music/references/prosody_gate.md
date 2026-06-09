<!-- agency-generated: v1 -->
# music.prosody_gate

Computed prosody gate — composes rhyme + syllable checks (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, lyrics, syllable_target (0 = skip).` |  |  |

## Returns

``{gate, passed, evidence}`` or typed GATE_FAILED.

## Chain-next

on failure, revise lyrics + re-check.

## Details

Passes iff rhyme_scheme has ≥ 2 groups (real rhyming, not all-A) AND (when syllable_target > 0) avg line syllables within ±2 of target. Records PASSED/BLOCKED_ON on the lifecycle via gate.check.

## Example

```bash
agency-music-prosody_gate --intent-id $IID …
```
