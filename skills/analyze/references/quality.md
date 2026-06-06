<!-- agency-generated: v1 -->
# analyze.quality

Decidable lint findings: unused imports, long lines, long functions, long files.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `path (str — file or dir), lang (str — only 'py' in v1).` |  |  |

## Returns

``{findings: [...], counts: {info, warn, fail}}``.

## Chain-next

``analyze.run`` to record findings as graph nodes.

## Details

(no further detail)

## Example

```bash
agency-analyze-quality --intent-id $IID …
```
