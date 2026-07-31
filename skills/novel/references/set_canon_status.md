<!-- agency-generated: v1 -->
# novel.set_canon_status

Stamp any node with a ``CANON_STATUS`` marker (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `node_id (any novel-domain node), status (canonical | proposal | quarry | gap).` |  |  |

## Returns

``{node_id, canon_status, was}``.

## Chain-next

``novel.canon_audit(novel_id)`` for the census.

## Details

(no further detail)

## Example

```bash
agency-novel-set_canon_status --intent-id $IID …
```
