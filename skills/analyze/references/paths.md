<!-- agency-generated: v1 -->
# analyze.paths

Spec 048 intent-path analysis: long chains + verb sequences.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `root_intent_id (str — empty = all user-owned roots), max_paths (int — cap when scanning all roots).` |  |  |

## Returns

``{findings: [...], counts: {info, warn, fail}}``.

## Chain-next

read findings to identify composite-verb candidates.

## Details

(no further detail)

## Example

```bash
agency-analyze-paths --intent-id $IID …
```
