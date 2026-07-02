<!-- agency-generated: v1 -->
# novel.apply_structure

Apply a structure template: mint one ``BeatExpectation`` per beat (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, template_id.` |  |  |

## Returns

``{novel_id, template_id, beat_count, minted, preserved}``.

## Chain-next

``novel.anchor_beat`` per drafted scene; ``novel.check_structure_coverage`` for the checklist.

## Details

(no further detail)

## Example

```bash
agency-novel-apply_structure --intent-id $IID …
```
