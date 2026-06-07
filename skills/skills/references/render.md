<!-- agency-generated: v1 -->
# skills.render

Render one skill to markdown at a chosen depth (progressive disclosure).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `skill_name (the skill to render); depth ('brief' = header + phase chain; 'full' = every phase with produces + gate); phase_index (≥0 → render only that one phase, full detail).` |  |  |

## Returns

``{markdown}`` — or ``{error}`` when the skill is unknown.

## Chain-next

``skills.lint`` to validate shape, or ``develop.skill_walk`` to drive it.

## Details

(no further detail)

## Example

```bash
agency-skills-render --intent-id $IID …
```
