<!-- agency-generated: v1 -->
# manage.list

LIST nodes of a ``label``, optionally filtered by exact-match ``where`` (Spec 293).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `label (str), where (dict|json-str — exact property match), live_only (bool — current-valid only).` |  |  |

## Returns

``{label, count, rows}``.

## Chain-next

manage.read(id) for one, or manage.update to mutate.

## Details

(no further detail)

## Example

```bash
agency-manage-list --intent-id $IID …
```
