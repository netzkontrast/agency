<!-- agency-generated: v1 -->
# plugin.lint_capability

Lint a capability against Hint #7 structural + role-tag + render-slice rules.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name (capability name registered in ``ctx.registry``).` |  |  |

## Returns

``{ok, violations, warnings, skipped, mode}``.

## Chain-next

fix violations + re-lint; ``mode=block`` is fatal.

## Details

(no further detail)

## Example

```bash
agency-plugin-lint_capability --intent-id $IID …
```
