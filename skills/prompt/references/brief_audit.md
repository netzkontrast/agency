<!-- agency-generated: v1 -->
# prompt.brief_audit

Rule-based clarity audit of a ResearchBrief (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `brief_id, min_score (default 70).` |  |  |

## Returns

``{audit_id, clarity_score, status, missing_sections}``.

## Chain-next

revise + re-audit OR ``prompt.brief_finalize``.

## Details

Scores 0-100 on heuristics: vague words → penalty; missing bracket markers → penalty; over default token budget → penalty. Below ``min_score`` records a BriefAudit with ``status='failed'``; else ``passed``.

## Example

```bash
agency-prompt-brief_audit --intent-id $IID …
```
