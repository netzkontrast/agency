<!-- agency-generated: v1 -->
# music.lyrics_pregen_gate

Composite lyrics pre-generation gate — chains 095's 4 lyric gates (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, album, lyrics (the lyric body to check).` |  |  |

## Returns

``{gate, passed, sub_gates}`` or typed GATE_FAILED.

## Chain-next

revise lyrics until all 4 sub-gates pass.

## Details

Composes prosody + pronunciation + repetition + explicit gates from Spec 095. Passes iff all 4 pass. The lifecycle_id is reused for each sub-gate so the audit trail is unified.

## Example

```bash
agency-music-lyrics_pregen_gate --intent-id $IID …
```
