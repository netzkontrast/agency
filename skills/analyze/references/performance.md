<!-- agency-generated: v1 -->
# analyze.performance

AST-based hot-path lint: nested O(n²), += in loop, unbounded while True.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `path (str — file or dir), lang (str — only 'py' in v1).` |  |  |

## Returns

``{findings: [...], counts: {info, warn, fail}}``.

## Chain-next

``analyze.run``.

## Details

(no further detail)

## Example

```bash
agency-analyze-performance --intent-id $IID …
```
