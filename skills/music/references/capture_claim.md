<!-- agency-generated: v1 -->
# music.capture_claim

Record a ResearchClaim node SERVES the intent (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `text, source_uri, domain (one of RESEARCH_DOMAINS), album, confidence (0..1 default 0.8).` |  |  |

## Returns

``{claim_id, text, domain, verified}``.

## Chain-next

``music.verify_sources`` to cross-check.

## Details

(no further detail)

## Example

```bash
agency-music-capture_claim --intent-id $IID …
```
