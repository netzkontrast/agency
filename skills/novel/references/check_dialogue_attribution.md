<!-- agency-generated: v1 -->
# novel.check_dialogue_attribution

Dialogue-tag check — plain ('said') vs flowery (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `body.` |  |  |

## Returns

``{passed, plain_count, flowery_count, flowery_hits}``.

## Chain-next

revise flowery hits then re-check.

## Details

Counts plain attributions (`said`/`asked`/etc.) vs flowery ones (`exclaimed`/`muttered`/etc.). Strunk & White: invisible is better. Passes when `flowery_count == 0`.

## Example

```bash
agency-novel-check_dialogue_attribution --intent-id $IID …
```
