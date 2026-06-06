<!-- agency-generated: v1 -->
# plugin.lint_skill

Lint a skill description against the CSO + length rules.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name (slug), description (the SKILL.md description field).` |  |  |

## Returns

``{ok, violations}``.

## Chain-next

fix violations + re-lint OR write the skill if ``ok=True``.

## Details

(no further detail)

## Example

```bash
agency-plugin-lint_skill --intent-id $IID …
```
