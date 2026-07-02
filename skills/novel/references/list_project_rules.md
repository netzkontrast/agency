<!-- agency-generated: v1 -->
# novel.list_project_rules

The rule registry (transform), optionally filtered by severity.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, severity (optional filter).` |  |  |

## Returns

``{rules: [{rule_id, name, severity, predicate_kind, rationale}], count}``.

## Chain-next

``novel.run_project_rules`` — the checklist executable.

## Details

(no further detail)

## Example

```bash
agency-novel-list_project_rules --intent-id $IID …
```
