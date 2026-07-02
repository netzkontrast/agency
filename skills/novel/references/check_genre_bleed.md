<!-- agency-generated: v1 -->
# novel.check_genre_bleed

The §11 genre-bleed rule (transform, soft): a chapter whose drafted ``genre_accent`` contradicts its block's accent is flagged — the author decides.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{passed, bleeds: [{chapter_number, chapter_accent, block_accent}]}``.

## Chain-next

re-accent the chapter or the block.

## Details

(no further detail)

## Example

```bash
agency-novel-check_genre_bleed --intent-id $IID …
```
