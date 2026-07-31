<!-- agency-generated: v1 -->
# novel.promote_from_quarry

Flip a quarry node → proposal + mint the Lock recording the promotion (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `node_id, source (what authorizes the promotion), topic (defaults to ``promote` |  | <kind>:<slug>``). |

## Returns

``{node_id, new_status, lock_id}``.

## Chain-next

validation, then ``novel.set_canon_status(node_id, 'canonical')`` when it locks.

## Details

(no further detail)

## Example

```bash
agency-novel-promote_from_quarry --intent-id $IID …
```
