<!-- agency-generated: v1 -->
# novel.list_claims

List captured claims; optional verified-status filter (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `verified (one of ``CLAIM_VERIFIED`` or ``""`` for all).` |  |  |

## Returns

``{claims, count}``.

## Chain-next

``novel.verify_sources`` for pending claims.

## Details

(no further detail)

## Example

```bash
agency-novel-list_claims --intent-id $IID …
```
