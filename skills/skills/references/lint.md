<!-- agency-generated: v1 -->
# skills.lint

Validate a skill's phase-graph shape — the structural contract a walk relies on.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `skill_name (the skill to validate).` |  |  |

## Returns

``{ok, violations: [str]}`` — non-empty phases, every phase has a unique integer index + a name, and any gate is 'hard'/'soft'.

## Chain-next

fix the schema where it is authored, then re-lint.

## Details

(no further detail)

## Example

```bash
agency-skills-lint --intent-id $IID …
```
