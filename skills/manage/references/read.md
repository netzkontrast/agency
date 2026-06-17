<!-- agency-generated: v1 -->
# manage.read

READ a node by id — its current properties + a ``live`` flag (False once retracted; Spec 293).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `node_id (str).` |  |  |

## Returns

``{id, labels, live, props}`` or ``{error}`` if absent.

## Chain-next

manage.update / manage.amend / manage.retract.

## Details

(no further detail)

## Example

```bash
agency-manage-read --intent-id $IID …
```
