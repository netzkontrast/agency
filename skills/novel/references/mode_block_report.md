<!-- agency-generated: v1 -->
# novel.mode_block_report

The §1 block table (transform): every block with mode / bridge target / genre; chapters in NO block are the unstaged surface.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{blocks: [{label, mode, from_chapter, to_chapter, bridge_frequency_target, genre_accent}], unstaged: [chapter_number]}``.

## Chain-next

``novel.define_mode_block`` for the unstaged spans.

## Details

(no further detail)

## Example

```bash
agency-novel-mode_block_report --intent-id $IID …
```
