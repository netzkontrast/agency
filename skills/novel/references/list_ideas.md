<!-- agency-generated: v1 -->
# novel.list_ideas

List captured ideas with an optional status filter (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `status (one of ``IDEA_STATUS`` or ``""`` for all).` |  |  |

## Returns

``{ideas: [...], count}``.

## Chain-next

``novel.promote_idea`` for any "new" idea ready to ship.

## Details

(no further detail)

## Example

```bash
agency-novel-list_ideas --intent-id $IID …
```
