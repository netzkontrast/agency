<!-- agency-generated: v1 -->
# novel.pending_verifications

Aggregate pending claims by domain (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `none.` |  |  |

## Returns

``{count, by_domain}`` — only claims with ``verified=="pending"``.

## Chain-next

``novel.dispatch_research`` (Slice 2) to fan out specialists.

## Details

(no further detail)

## Example

```bash
agency-novel-pending_verifications --intent-id $IID …
```
