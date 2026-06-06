<!-- agency-generated: v1 -->
# analyze.security

Decidable security patterns: eval/exec, hardcoded credentials, pickle.load, shell=True.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `path (str — file or dir), lang (str — only 'py' in v1).` |  |  |

## Returns

``{findings: [...], counts: {info, warn, fail}}``.

## Chain-next

``analyze.run`` to record findings.

## Details

(no further detail)

## Example

```bash
agency-analyze-security --intent-id $IID …
```
