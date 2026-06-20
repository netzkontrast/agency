<!-- agency-generated: v1 -->
# frugal.review

Review for over-engineering ONLY (delete/stdlib/native/yagni/shrink) — distinct from analyze's multi-axis pass.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scope ("diff"|"repo"), ref (str — diff base, default HEAD), paths (str).` |  |  |

## Returns

token-bounded ``{scope, files, decidable_findings: [top-N {tag, rule, file, line, message}], tags, note}``.

## Chain-next

apply the cuts; ``frugal.review`` again; ``frugal.debt`` for deferrals.

## Details

(no further detail)

## Example

```bash
agency-frugal-review --intent-id $IID …
```
