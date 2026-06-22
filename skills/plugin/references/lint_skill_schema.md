<!-- agency-generated: v1 -->
# plugin.lint_skill_schema

Strict per-type + self-containment + no-stub + verb-resolves lint over a 371 Skill dict (Spec 377) — beyond the SkillDoc shape ``lint_skill`` checks.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `skill (a Skill dict — name, kind, type?, description?, phases?, …).` |  |  |

## Returns

``{ok, violations: [{rule, message}]}``.

## Chain-next

fix the flagged sections + re-lint; ``install.generate`` / ``check-drift`` gate on this (graduated warn→block, Slice 2).

## Details

(no further detail)

## Example

```bash
agency-plugin-lint_skill_schema --intent-id $IID …
```
