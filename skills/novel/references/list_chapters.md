<!-- agency-generated: v1 -->
# novel.list_chapters

List a novel's chapters ordered by number (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{chapters: [{chapter_id, number, title, status}], count}``.

## Chain-next

``novel.set_chapter_status`` or ``novel.create_scene``.

## Details

(no further detail)

## Example

```bash
agency-novel-list_chapters --intent-id $IID …
```
