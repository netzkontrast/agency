<!-- agency-generated: v1 -->
# novel.export_pdf

Render manuscript + write PDF via FormatDriver (effect).

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
agency-novel-export_pdf --intent-id $IID …
```
