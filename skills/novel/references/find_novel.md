<!-- agency-generated: v1 -->
# novel.find_novel

Substring-match novel titles (transform, driver-free).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `query (case-insensitive substring; ``""`` returns all).` |  |  |

## Returns

``{novels: [{novel_id, title, author, status}], count}``.

## Chain-next

``novel.set_novel_status`` or ``novel.render_manuscript``.

## Details

(no further detail)

## Example

```bash
agency-novel-find_novel --intent-id $IID …
```
