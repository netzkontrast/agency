<!-- agency-generated: v1 -->
# plugin.author_skill

Render a CSO-compliant SKILL.md.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name (skill slug), description (trigger phrase), body (markdown).` |  |  |

## Returns

``{result: <skill_md_str>}``.

## Chain-next

``plugin.lint_skill(name=, description=)`` then write.

## Details

(no further detail)

## Example

```bash
agency-plugin-author_skill --intent-id $IID …
```
