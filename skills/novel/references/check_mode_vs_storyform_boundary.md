<!-- agency-generated: v1 -->
# novel.check_mode_vs_storyform_boundary

The KP's load-bearing distinction (transform): mode-changes are NOT storyform boundaries.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{passed, violations: [{transition_id, at_chapter, block_label, reason}]}``.

## Chain-next

retag the transition or move the block edge.

## Details

(no further detail)

## Example

```bash
agency-novel-check_mode_vs_storyform_boundary --intent-id $IID …
```
