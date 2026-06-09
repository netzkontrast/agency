<!-- agency-generated: v1 -->
# music.list_claims

List ResearchClaim nodes (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, status (one of RESEARCH_CLAIM_VERIFIED).` |  |  |

## Returns

``{claims, count, album, status}``.

## Chain-next

``music.verify_sources``.

## Details

(no further detail)

## Example

```bash
agency-music-list_claims --intent-id $IID …
```
