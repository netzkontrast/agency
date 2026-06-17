<!-- agency-generated: v1 -->
# manage.update

UPDATE a node in place — a bi-temporal revision, stable id (Spec 293).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `node_id (str), props (dict|json-str — merged onto the node).` |  |  |

## Returns

``{id, updated}`` or ``{error}``.

## Chain-next

manage.read(id) to confirm.

## Details

(no further detail)

## Example

```bash
agency-manage-update --intent-id $IID …
```
