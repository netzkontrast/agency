<!-- agency-generated: v1 -->
# develop.validate_skill

Validate a capability's Agent-Skill (its SkillDoc) — lint + dry-run emit.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name (capability name; "" validates ALL caps that declare a skill_doc).` |  |  |

## Returns

``{ok, results: {<cap>: {ok, violations:[…], skill_doc: bool}}}`` — ``ok`` is the AND across the validated caps.

## Chain-next

fix violations in the capability's SkillDoc, then re-validate.

## Details

Spec 080 — the skill-authoring validation surface (dogfood, not a script): runs ``plugin.lint_skill_doc`` AND a dry-run ``emit_skill`` (which catches frontmatter/reference problems) against a capability's ``skill_doc``, so an author confirms a capability is a complete Agent Skill before commit. The ``authoring-capabilities`` discipline calls this before its commit gate.

## Example

```bash
agency-develop-validate_skill --intent-id $IID …
```
