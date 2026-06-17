<!-- agency-generated: v1 -->
# manage.retract

RETRACT — bi-temporal SOFT delete: close the node's valid window so current reads drop it, history retained (Spec 293).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `node_id (str).` |  |  |

## Returns

``{id, retracted, as_of}`` or ``{error}``.

## Chain-next

manage.read(id) → ``live: False``; manage.list excludes it.

## Details

(no further detail)

## Example

```bash
agency-manage-retract --intent-id $IID …
```
