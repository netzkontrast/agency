<!-- agency-generated: v1 -->
# novel.create_novel

Record a Novel node SERVING the intent; materialise disk on production.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `title, author, genre (default "novel"; routes the disk layout `works/{author}/works/{genre}/{slug}/`).` |  |  |

## Returns

``{novel_id, title, status, work_path?}`` — ``work_path`` appears when the production driver is wired (Spec 121).

## Chain-next

``novel.create_chapter`` once outline is ready.

## Details

(no further detail)

## Example

```bash
agency-novel-create_novel --intent-id $IID …
```
