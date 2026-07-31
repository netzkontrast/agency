<!-- agency-generated: v1 -->
# novel.check_structure_coverage

The author's checklist: which beats are anchored to scenes, which still await one (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{anchored, unanchored: [{beat_slug, name, target_position}]}``.

## Chain-next

``novel.anchor_beat`` for each unanchored beat.

## Details

(no further detail)

## Example

```bash
agency-novel-check_structure_coverage --intent-id $IID …
```
