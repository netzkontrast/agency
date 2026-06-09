<!-- agency-generated: v1 -->
# music.document_hunt

Dispatch a document-hunter specialist via agency.research (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `query, domain (default ``document_hunter``).` |  |  |

## Returns

``{research_id, query, domain}``.

## Chain-next

``music.capture_claim`` per found document.

## Details

(no further detail)

## Example

```bash
agency-music-document_hunt --intent-id $IID …
```
