<!-- agency-generated: v1 -->
# manage.amend

AMEND append-only — close the old version, create a new one linked ``SUPERSEDED_BY`` (Spec 293).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `node_id (str), changes (dict|json-str).` |  |  |

## Returns

``{old_id, new_id}`` or ``{error}``.

## Chain-next

manage.read(new_id); the old id remains queryable as history.

## Details

(no further detail)

## Example

```bash
agency-manage-amend --intent-id $IID …
```
