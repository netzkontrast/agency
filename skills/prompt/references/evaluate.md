<!-- agency-generated: v1 -->
# prompt.evaluate

Goal-aware multi-dimension evaluation of a prompt body (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `prompt_body (str), target (str — a registered profile; ``user-prompt`` default), min_score (float — 0-10 pass line).` |  |  |

## Returns

``{target, scores: {dim: 0-10, ...}, overall, flags: [...], status: 'passed'|'failed'}`` OR ``{target, error: 'UNKNOWN_TARGET', available: [...]}``.

## Chain-next

revise + re-evaluate; ``develop.optimize_skilldoc`` for a functional target (306).

## Details

Supersedes ``audit`` (which stays a back-compat alias with its own contract): ``evaluate`` scores against a criteria PROFILE selected by ``target``. ``user-prompt`` runs the 5-dimension grid (clarity / specificity / context / completeness / structure). Spec 306 adds the ``skilldoc`` / ``tool-desc`` / ``template`` functional profiles whose flags name the target goal they violate.

## Example

```bash
agency-prompt-evaluate --intent-id $IID …
```
