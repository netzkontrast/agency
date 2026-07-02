<!-- agency-generated: v1 -->
# novel.run_project_rules

Run EVERY registered R-rule over one scene (transform) — the §10.3 per-scene self-review checklist made executable.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id.` |  |  |

## Returns

``{passed, findings: [{rule_id, severity, message}]}`` — ``passed`` is False only on findings (any severity).

## Chain-next

fix critical findings (strike/rewrite); medium/low go to the reviewer.

## Details

(no further detail)

## Example

```bash
agency-novel-run_project_rules --intent-id $IID …
```
