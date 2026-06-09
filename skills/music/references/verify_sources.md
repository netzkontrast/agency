<!-- agency-generated: v1 -->
# music.verify_sources

Cross-check pending claims (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album (optional slug — empty = all pending).` |  |  |

## Returns

``{verified_count, rejected_count, still_pending}``.

## Chain-next

``music.human_signoff`` for terminal review.

## Details

Iterates pending ResearchClaim nodes, flips verified status, records a VerificationRecord per claim. Production calls research.verify per research_id; the stub here just optimistically confirms.

## Example

```bash
agency-music-verify_sources --intent-id $IID …
```
