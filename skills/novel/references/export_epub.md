<!-- agency-generated: v1 -->
# novel.export_epub

Render manuscript + write epub via FormatDriver (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{format, path, artefact_id}``; typed DEPENDENCY_MISSING when no FormatDriver is wired (production flag off).

## Chain-next

``novel.publication_gate``.

## Details

(no further detail)

## Example

```bash
agency-novel-export_epub --intent-id $IID …
```
