<!-- agency-generated: v1 -->
# loop.add_member

Add a council member (reviewer|judge) bound to a model family to a loop (365).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `loop_id (str), role (reviewer|judge), scope (plan|delivery|both), family (str), local (bool), driver (str), mid (str — optional id).` |  |  |

## Returns

``{member_id, role, family}``.

## Chain-next

loop.recommend_council(loop_id) to check the verdict-source rule.

## Details

(no further detail)

## Example

```bash
agency-loop-add_member --intent-id $IID …
```
