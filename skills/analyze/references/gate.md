<!-- agency-generated: v1 -->
# analyze.gate

Record the quality gate verdict as an auditable Gate node (Spec 382 §2).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `score (int), critical (int — critical-tier finding count), min_score / max_critical (int — tunable budgets), mode (str).` |  |  |

## Returns

{passed, blocked, evidence, gate, name}.

## Chain-next

gate.verdict("quality:<mode>") — non-zero exit on a block in CI.

## Details

PASSED iff ``score >= min_score`` AND ``critical <= max_critical`` — documented tunable budgets (rule 8). Records a ``Gate{name:"quality:<mode>", passed, evidence}`` SERVING the intent — auditable provenance, unlike brooks' bare ``ci-gate.mjs`` exit code. The headless CI twin computes the score (analyze.score) then calls this; ``gate.verdict`` reads it back. Use when: gating a PR/commit on the Health Score + critical count.

## Example

```bash
agency-analyze-gate --intent-id $IID …
```
