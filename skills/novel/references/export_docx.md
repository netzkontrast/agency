<!-- agency-generated: v1 -->
# novel.export_docx

Render manuscript + write docx via FormatDriver (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{format, path, artefact_id}``; typed DEPENDENCY_MISSING when no FormatDriver is wired.

## Chain-next

``novel.publication_gate``.

## Details

(no further detail)

## Example

```bash
agency-novel-export_docx --intent-id $IID …
```
