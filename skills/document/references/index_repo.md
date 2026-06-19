<!-- agency-generated: v1 -->
# document.index_repo

Deterministic repo briefing.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `path (str), apply (bool — write COMPLETE PROJECT_INDEX.md), max_tokens (int — preview budget; default 3000).` |  |  |

## Returns

``{index_id, content, tokens, files_scanned, writeup}``.

## Chain-next

caller publishes via ``apply=True`` after review.

## Details

(no further detail)

## Example

```bash
agency-document-index_repo --intent-id $IID …
```
