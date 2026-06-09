<!-- agency-generated: v1 -->
# novel.set_novel_status

Flip a Novel's lifecycle status; enum-checked (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, status (one of ``NOVEL_STATUS``).` |  |  |

## Returns

``{novel_id, status}``.

## Chain-next

continue per the new lifecycle phase.

## Details

(no further detail)

## Example

```bash
agency-novel-set_novel_status --intent-id $IID …
```
