<!-- agency-generated: v1 -->
# manage.create

CREATE a node of any ontology ``label``; SERVES the intent (Spec 293).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `label (str — an ontology node label), props (dict|json-str — the node's properties; validated against the ontology).` |  |  |

## Returns

``{id, label}`` or ``{error}`` on an ontology violation.

## Chain-next

manage.read(id) to confirm; manage.update to mutate.

## Details

(no further detail)

## Example

```bash
agency-manage-create --intent-id $IID …
```
