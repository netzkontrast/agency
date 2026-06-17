<!-- agency-generated: v1 -->
# skill_generator.generate

Author a SKILL.md and lint it against the CSO rules, flagging if not deploy-ready.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name (skill slug), description (str — the trigger phrase), body (str — the SKILL.md content).` |  |  |

## Returns

``{name, skill_md, ok, violations}`` (wire shape).

## Chain-next

caller writes ``skills/<name>/SKILL.md`` if ``ok=True``; otherwise iterates on ``violations``.

## Details

(no further detail)

## Example

```bash
agency-skill_generator-generate --intent-id $IID …
```
