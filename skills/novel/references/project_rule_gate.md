<!-- agency-generated: v1 -->
# novel.project_rule_gate

Composite manuscript gate (transform): fails iff any scene carries a finding AT or ABOVE ``block_at``; lower severities surface as warnings (§10.2 — critical strikes, medium/low reviewer-check).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, block_at (critical|medium|low).` |  |  |

## Returns

``{passed, blocking: [{scene_id, rule_id, severity, message}], warnings: [...]}``.

## Chain-next

rewrite the blocking scenes; re-run.

## Details

(no further detail)

## Example

```bash
agency-novel-project_rule_gate --intent-id $IID …
```
