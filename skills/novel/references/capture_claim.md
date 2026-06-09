<!-- agency-generated: v1 -->
# novel.capture_claim

Record a NovelClaim node SERVING the intent (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `text, source_uri, domain (one of ``RESEARCH_DOMAINS``).` |  |  |

## Returns

``{claim_id, text, domain, verified}``.

## Chain-next

``novel.verify_sources`` (Slice 2) to cross-check.

## Details

(no further detail)

## Example

```bash
agency-novel-capture_claim --intent-id $IID …
```
