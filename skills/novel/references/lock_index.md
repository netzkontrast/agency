<!-- agency-generated: v1 -->
# novel.lock_index

The Master-Index of active locks (transform) — consulted before any contested drafting decision.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, topic (optional filter).` |  |  |

## Returns

``{locks, count, by_topic}``.

## Chain-next

``novel.resolve_canon_conflict`` on competing facts.

## Details

(no further detail)

## Example

```bash
agency-novel-lock_index --intent-id $IID …
```
