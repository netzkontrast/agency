<!-- agency-generated: v1 -->
# music.verify_gate

Computed verification gate — composes pending_verifications (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, album.` |  |  |

## Returns

``{gate, passed, pending_count}`` or typed GATE_FAILED.

## Chain-next

on fail, ``music.verify_sources`` to clear pending.

## Details

Passes iff zero pending claims for the album.

## Example

```bash
agency-music-verify_gate --intent-id $IID …
```
