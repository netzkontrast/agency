<!-- agency-generated: v1 -->
# music.lyrics_pregen_gate

Composite lyrics pre-generation gate — chains the lyric gates (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, album, lyrics (the lyric body to check).` |  |  |

## Returns

``{gate, passed, sub_gates}`` or typed GATE_FAILED.

## Chain-next

revise lyrics until all 4 sub-gates pass.

## Details

Composes prosody + pronunciation + repetition + explicit (Spec 095) + name-exposure (Spec 119) sub-gates. Passes iff all pass. The name-exposure sub-gate is a no-op pass for rosterless projects (empty ``name_exposure.blocklist``). The lifecycle_id is reused for each sub-gate so the audit trail is unified.

## Example

```bash
agency-music-lyrics_pregen_gate --intent-id $IID …
```
