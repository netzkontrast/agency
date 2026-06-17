<!-- agency-generated: v1 -->
# doctrine.cite

Record that a principle or rule DROVE an action — a DoctrineCitation SERVING the intent (auditable provenance, Spec 303).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name (str — a known principle or rule name), rationale (str — why it applied; optional).` |  |  |

## Returns

``{citation_id, name, kind}`` or ``{error}`` for an unknown name.

## Chain-next

the cited principle is now queryable provenance on the intent.

## Details

(no further detail)

## Example

```bash
agency-doctrine-cite --intent-id $IID …
```
