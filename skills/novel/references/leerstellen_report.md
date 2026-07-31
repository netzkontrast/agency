<!-- agency-generated: v1 -->
# novel.leerstellen_report

List the registered deliberate gaps (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{gaps: [{leerstelle_id, scene_id, kind, note}], count, by_kind}``.

## Chain-next

hand the list to the editorial pipeline as do-not-fix context.

## Details

(no further detail)

## Example

```bash
agency-novel-leerstellen_report --intent-id $IID …
```
