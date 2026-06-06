<!-- agency-generated: v1 -->
# analyze.architecture

Dependency-graph + structural checks: import cycles, file LOC thresholds.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `path (str — file or package root).` |  |  |

## Returns

``{findings: [...], counts: {info, warn, fail}}``.

## Chain-next

``analyze.run``.

## Details

(no further detail)

## Example

```bash
agency-analyze-architecture --intent-id $IID …
```
