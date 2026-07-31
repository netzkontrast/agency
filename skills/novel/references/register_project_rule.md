<!-- agency-generated: v1 -->
# novel.register_project_rule

Author an R-rule (effect) — upsert keyed by (novel, rule_id).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, rule_id (stable handle, e.g. "R-5"), name, severity (critical|medium|low), predicate_kind (mutual-exclusion|per-scene-budget|forbidden-verbatim| register-forbidden), params (the predicate's config dict), rationale.` |  |  |

## Returns

``{rule_node_id, rule_id, was_update}``.

## Chain-next

``novel.run_project_rules(scene_id)`` per scene.

## Details

(no further detail)

## Example

```bash
agency-novel-register_project_rule --intent-id $IID …
```
